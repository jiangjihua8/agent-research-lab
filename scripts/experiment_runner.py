"""Sequential POSIX experiment runner. Commands are argv arrays, never shell strings."""

import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import time


TERMINATION_MARGIN = 5


def preflight(project, job, api):
    key, protocol = api.current(project)
    api.require(isinstance(job, dict), "job 必须为对象")
    run_id = api.identifier(job.get("id"), "job.id")
    api.require(not (project / "runs" / run_id).exists() and not (project / "executions" / run_id).exists(), f"运行 id 已存在: {run_id}")
    api.require(job.get("protocol_sha256") == key, "job 未绑定当前协议")
    api.require(job.get("kind") in ("smoke", "pilot", "confirmatory"), "job.kind 无效")
    api.require(job.get("model_id") in {x["id"] for x in api.models(protocol)}, "job.model_id 未登记")
    api.require(job.get("dataset_id") in {x["id"] for x in protocol["datasets"]}, "job.dataset_id 未登记")
    api.require(type(job.get("seed")) is int and job["seed"] in protocol["seeds"], "job.seed 未登记")
    api.require(type(job.get("gpu_count")) is int and job["gpu_count"] >= 0, "job.gpu_count 需要非负整数")
    api.number(job.get("timeout_seconds"), "job.timeout_seconds", minimum=0.01)
    argv = api.array(job.get("argv"), "job.argv")
    api.require(all(isinstance(x, str) and x and "\x00" not in x for x in argv), "argv 使用非空字符串数组")
    api.fields(job, ("code_revision", "code_artifact", "environment_file"), "job")
    api.artifact(project, job["code_artifact"])
    if "intent_file" in job:
        api.artifact(project, job["intent_file"])
    environment = api.artifact(project, job["environment_file"])
    frozen = api.read_json(project / "protocols" / f"{key}.json")["snapshot"]
    api.require(api.file_hash(environment) == frozen["inputs"][protocol["environment_file"]], "job 环境不匹配冻结协议")
    split = job.get("evaluation_split")
    expected = ("train", "validation") if job["kind"] == "smoke" else (("validation",) if job["kind"] == "pilot" else ("test",))
    api.require(split in expected, f"{job['kind']} 的 evaluation_split 必须为 {expected}")
    records = api.runs(project)
    # Candidate exploration uses the established baseline gate. Baseline calibration
    # itself must remain possible before that gate can be passed.
    is_baseline = job["model_id"] in {x["id"] for x in protocol["baselines"]}
    model = next(x for x in api.models(protocol) if x["id"] == job["model_id"])
    if "code_artifact" in model:
        api.require(api.file_hash(api.artifact(project, job["code_artifact"])) == frozen["inputs"][model["code_artifact"]], "运行代码快照与模型冻结版本不一致")
    if not is_baseline or job["kind"] == "confirmatory":
        api.require_checks(project, "pilot")
    if job["kind"] == "confirmatory":
        api.require("code_artifact" in model and "config_file" in model, "正式执行前在 protocol 的模型条目冻结 code_artifact 和 config_file")
        api.require(any(x["protocol_sha256"] == key and x["model_id"] == job["model_id"]
                        and x["dataset_id"] == job["dataset_id"] and x["kind"] == "pilot"
                        and x["status"] == "completed" for x in records), "正式运行前需要该模型/数据集的 pilot")
        api.require(not any(x["protocol_sha256"] == key and x["kind"] == "confirmatory" and x["status"] == "completed"
                            and all(x[k] == job[k] for k in ("model_id", "dataset_id", "seed")) for x in records), "正式实验单元已完成")
    return {"elapsed_seconds": job["timeout_seconds"] + TERMINATION_MARGIN,
            "gpu_hours": (job["timeout_seconds"] + TERMINATION_MARGIN) * job["gpu_count"] / 3600}


def stop_process_group(process):
    """Stop descendants as well as the training parent, even if the parent exits first."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_one(project, job, api):
    preflight(project, job, api)
    output = project / "executions" / job["id"]
    output.mkdir(parents=True)
    api.write_json(output / "job.json", job)
    source = api.artifact(project, job["code_artifact"])
    archived_code = output / ("source" + source.suffix)
    shutil.copy2(source, archived_code)
    archived_environment = output / "environment.txt"
    shutil.copy2(api.artifact(project, job["environment_file"]), archived_environment)
    archived_intent = None
    if "intent_file" in job:
        intent = api.artifact(project, job["intent_file"])
        archived_intent = output / ("intent" + intent.suffix)
        shutil.copy2(intent, archived_intent)
    protocol = api.current(project)[1]
    model = next(x for x in api.models(protocol) if x["id"] == job["model_id"])
    archived_config = None
    if "config_file" in model:
        config = api.artifact(project, model["config_file"])
        archived_config = output / ("config" + config.suffix)
        shutil.copy2(config, archived_config)
    api.write_json(output / "started.json", {"started_at": api.now(), "pid": os.getpid(), "protocol_sha256": job["protocol_sha256"]})
    environment = os.environ.copy()
    environment.update(RESEARCH_OUTPUT_DIR=str(output), RESEARCH_SEED=str(job["seed"]),
                       RESEARCH_MODEL_ID=job["model_id"], RESEARCH_DATASET_ID=job["dataset_id"],
                       RESEARCH_EVALUATION_SPLIT=job["evaluation_split"], RESEARCH_PROTOCOL_SHA256=job["protocol_sha256"])
    failure = ""
    process = None
    started = time.monotonic()
    previous_sigterm = signal.getsignal(signal.SIGTERM)

    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    try:
        with (output / "stdout.log").open("w", encoding="utf-8") as log:
            log.write(f"Command: {shlex.join(job['argv'])}\nWorking directory: {project}\n")
            log.flush()
            try:
                process = subprocess.Popen(job["argv"], cwd=project, env=environment, stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                returncode = process.wait(timeout=job["timeout_seconds"])
                if returncode:
                    failure = f"进程退出码 {returncode}"
            except subprocess.TimeoutExpired:
                failure = f"超过 timeout_seconds={job['timeout_seconds']}"
            except KeyboardInterrupt:
                failure = "运行被中断"
            except OSError as exc:
                failure = f"启动失败: {exc}"
            finally:
                if process is not None:
                    stop_process_group(process)
            log.write(f"\nRunner outcome: {failure or 'process completed; checking metrics'}\n")
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
    elapsed = max(time.monotonic() - started, 0.000001)
    if not failure:
        try:
            metrics = api.read_json(output / "metrics.json")
            metric = api.current(project)[1]["primary_metric"]["name"]
            api.require(bool(metrics), "metrics.json 为空")
            if job["kind"] != "smoke":
                api.require(metric in metrics, "metrics.json 缺少主指标")
            for name, value in metrics.items():
                api.number(value, f"metric.{name}", minimum=-float("1.7976931348623157e308"))
        except (api.Problem, OSError, KeyError, ValueError) as exc:
            failure = f"结果无效: {exc}"
    data = {key: job[key] for key in ("id", "protocol_sha256", "kind", "model_id", "dataset_id", "seed", "gpu_count", "code_revision", "evaluation_split")}
    relative = output.relative_to(project)
    data.update(status="failed" if failure else "completed", failure_reason=failure, elapsed_seconds=elapsed,
                command=shlex.join(job["argv"]) + f" (cwd={project}; RESEARCH_* 见 executions/{job['id']}/job.json)",
                code_artifact=str(archived_code.relative_to(project)), environment_file=str(archived_environment.relative_to(project)),
                log_file=str(relative / "stdout.log"), metrics_file=str(relative / "metrics.json"), notes=job.get("notes", ""))
    if archived_config is not None:
        data["config_file"] = str(archived_config.relative_to(project))
    if archived_intent is not None:
        data["intent_file"] = str(archived_intent.relative_to(project))
    api.write_json(output / "record-input.json", data)
    # If protocol or archival validation fails, raw output remains. Subsequent
    # execute calls refuse unregistered executions, preventing uncounted retries.
    result = api.record(argparse.Namespace(project=project, file=output / "record-input.json"))
    return 1 if failure or result else 0


def execute(args, api):
    project = args.project.resolve()
    api.require(os.name == "posix", "本地 execute 需要 POSIX 进程组；其他系统使用原有调度器 + record")
    payload = api.read_json(args.file)
    jobs = api.array(payload["jobs"], "plan.jobs") if "jobs" in payload else [payload]
    lock = project / ".execution.lock"
    api.require(not lock.exists(), "有执行锁；先确认当前任务结束，硬中断时核对 executions 和进程后再清理锁")
    unresolved = [p.name for p in (project / "executions").glob("*") if p.is_dir() and not (project / "runs" / p.name / "record.json").is_file()]
    api.require(not unresolved, f"存在未登记的执行，先按真实消耗恢复记录: {unresolved}")
    reservations = [preflight(project, job, api) for job in jobs]
    ids = [j["id"] for j in jobs]
    api.require(len(ids) == len(set(ids)), "计划含重复 run id")
    formal = [(j["model_id"], j["dataset_id"], j["seed"]) for j in jobs if j["kind"] == "confirmatory"]
    api.require(len(formal) == len(set(formal)), "计划含重复正式实验单元")
    issues = api.budget_issues(project, api.runs(project) + reservations)
    api.require(not issues, "计划最大消耗超过剩余预算（含终止余量）: " + "; ".join(issues))
    if args.dry_run:
        print(json.dumps({"ready": True, "jobs": ids, "max_wall_hours": sum(x["elapsed_seconds"] for x in reservations) / 3600,
                          "max_gpu_hours": sum(x["gpu_hours"] for x in reservations)}, ensure_ascii=False, indent=2))
        return 0
    # Serialize managed runners for the entire plan. Other record/freeze commands
    # must follow the documented single-writer contract.
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()) + "\n")
    try:
        for job in jobs:
            reservation = preflight(project, job, api)
            issues = api.budget_issues(project, api.runs(project) + [reservation])
            api.require(not issues, "; ".join(issues))
            print(f"开始 {job['id']}: {job['kind']} / {job['model_id']} / {job['dataset_id']}", flush=True)
            if run_one(project, job, api):
                print("计划停止：本次失败或超预算。先检查日志、做出下一步决策，再运行新计划。")
                return 1
        return 0
    finally:
        lock.unlink(missing_ok=True)
