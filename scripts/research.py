#!/usr/bin/env python3
"""Research workflow, bounded local experiments, and traceable evidence (Python stdlib)."""

import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import sys
import tempfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
STAGES = ("scope", "literature", "hypothesis", "protocol", "pilot", "experiments", "paper", "submission")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
PILOT_CHECKS = ("data_leakage", "metric_correctness", "evaluator_sensitivity", "gradient_or_equivalent", "tiny_overfit", "baseline_reproduction")
REVIEW_INPUTS = {
    "pilot": ("pilot.json",),
    "experiments": ("reports/summary.json", "reports/analysis.md"),
    "paper": ("claims.json", "literature.json", "paper/manuscript.md", "paper/references.bib", "reports/summary.json"),
}
SUBMISSION_CHECKS = ("format", "anonymity", "citations", "ai_policy", "licenses_and_ethics", "reproducibility", "visual_qa")


class Problem(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Problem(message)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(canonical(data)).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def no_constant(value):
    raise Problem(f"JSON 不允许非有限数字: {value}")


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"), parse_constant=no_constant)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise Problem(f"无法读取 {path}: {exc}") from exc
    require(isinstance(data, dict), f"{path}: 顶层必须是 JSON 对象")
    return data


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def string(value):
    return isinstance(value, str) and bool(value.strip()) and "{{" not in value


def fields(data, keys, label):
    require(isinstance(data, dict), f"{label}: 必须是对象")
    for key in keys:
        require(string(data.get(key)), f"{label}.{key}: 需要填写具体内容")


def array(value, label, nonempty=True):
    require(isinstance(value, list) and (bool(value) or not nonempty), f"{label}: 需要{'非空' if nonempty else ''}数组")
    return value


def number(value, label, minimum=0):
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum, f"{label}: 需要 >= {minimum} 的有限数字")
    return value


def identifier(value, label):
    require(isinstance(value, str) and bool(IDENTIFIER.fullmatch(value)), f"{label}: 使用字母、数字、点、下划线、连字符，最长 80 字符")
    return value


def artifact(project, name):
    require(isinstance(name, str) and string(name) and not Path(name).is_absolute(), "证据路径必须是项目内相对路径")
    path = (project / name).resolve()
    require(path.is_relative_to(project.resolve()), f"证据路径越界: {name}")
    require(path.is_file() and path.stat().st_size > 0, f"证据文件不存在或为空: {name}")
    return path


def fingerprints(project, names):
    return {name: file_hash(artifact(project, name)) for name in names}


def metadata(project):
    data = read_json(project / "project.json")
    require(data.get("schema_version") == 1, "不支持的 project.json schema_version")
    require(data.get("stage") in STAGES, "project.stage 无效")
    return data


def models(protocol):
    return list(itertools.chain.from_iterable(protocol.get(key, []) for key in ("baselines", "candidates", "ablations")))


def check_scope(project):
    data = metadata(project)
    fields(data, ("topic", "research_question", "contribution", "constraints"), "project")
    budget = data.get("budget")
    require(isinstance(budget, dict), "project.budget 必须是对象")
    require(type(budget.get("max_runs")) is int and budget["max_runs"] > 0, "budget.max_runs 需要正整数")
    number(budget.get("max_gpu_hours"), "budget.max_gpu_hours")
    number(budget.get("max_gpu_hours_per_run"), "budget.max_gpu_hours_per_run")
    for name in ("max_wall_hours", "max_wall_hours_per_run"):
        if name in budget:
            number(budget[name], f"budget.{name}")


def check_literature(project):
    data = read_json(project / "literature.json")
    fields(data, ("synthesis",), "literature")
    for entry in array(data.get("searches"), "literature.searches"):
        fields(entry, ("query", "source", "searched_at"), "search")
    ids = []
    direct = False
    for paper in array(data.get("papers"), "literature.papers"):
        fields(paper, ("id", "title", "url", "problem", "mechanism", "evidence", "limitations", "accessed_at"), "paper")
        identifier(paper["id"], "paper.id")
        require(paper["url"].startswith(("https://", "http://")), "paper.url 需要可核查的原始来源 URL")
        require(paper.get("source_checked") is True, f"{paper['id']}: 原始来源尚未核查")
        require(paper.get("relevance") in ("direct", "transfer", "context"), "paper.relevance 无效")
        require(paper.get("read_status") in ("abstract", "full"), "paper.read_status 无效")
        direct |= paper["relevance"] == "direct" and paper["read_status"] == "full"
        ids.append(paper["id"])
    require(len(ids) == len(set(ids)), "论文 id 重复")
    require(direct, "至少需要一篇直接相关且读过全文的工作；这只是结构下限，不代表检索充分")


def check_hypothesis(project):
    data = read_json(project / "hypothesis.json")
    fields(data, ("baseline_failure", "explanation", "intervention", "falsification", "novelty", "evidence_cost"), "hypothesis")
    for key in ("predictions", "alternatives", "related_work_ids"):
        require(all(string(x) for x in array(data.get(key), f"hypothesis.{key}")), f"hypothesis.{key} 需要非空字符串")
    papers = {x["id"] for x in read_json(project / "literature.json").get("papers", [])}
    require(set(data["related_work_ids"]) <= papers, "假设引用了 literature.json 中不存在的工作")


def validate_protocol(project):
    data = read_json(project / "protocol.json")
    metric = data.get("primary_metric")
    fields(metric, ("name", "direction"), "protocol.primary_metric")
    require(metric["direction"] in ("min", "max"), "metric.direction 必须为 min 或 max")
    seeds = array(data.get("seeds"), "protocol.seeds")
    require(all(type(x) is int and x >= 0 for x in seeds) and len(seeds) == len(set(seeds)), "seeds 需要不重复的非负整数")
    fields(data, ("uncertainty", "environment_file", "evaluation_file"), "protocol")
    fairness = data.get("fairness")
    fields(fairness, ("axis", "rationale", "tuning_policy", "capacity_control"), "protocol.fairness")
    require(fairness.get("selection_split") == "validation", "模型/超参选择必须在 validation，不能用 test")
    dataset_ids, paths = [], [data["environment_file"], data["evaluation_file"]]
    for dataset in array(data.get("datasets"), "protocol.datasets"):
        fields(dataset, ("id", "version", "split_manifest"), "dataset")
        identifier(dataset["id"], "dataset.id")
        dataset_ids.append(dataset["id"])
        paths.append(dataset["split_manifest"])
    require(len(dataset_ids) == len(set(dataset_ids)), "dataset.id 重复")
    model_ids = []
    for kind in ("baselines", "candidates", "ablations"):
        for model in array(data.get(kind), f"protocol.{kind}", nonempty=kind == "baselines"):
            fields(model, ("id", "rationale", "tuning_budget"), kind)
            model_ids.append(identifier(model["id"], "model.id"))
            for name in ("code_artifact", "config_file"):
                if name in model:
                    fields(model, (name,), kind)
                    paths.append(model[name])
    require(len(model_ids) == len(set(model_ids)), "baseline/candidate/ablation 的 id 必须全局唯一")
    fields(data, ("ablation_rationale", "stopping_rule"), "protocol")
    fingerprints(project, paths)
    return data, paths


def snapshot(project):
    data = metadata(project)
    protocol, paths = validate_protocol(project)
    return {
        "research_question": data["research_question"], "contribution": data["contribution"],
        "budget": data["budget"], "hypothesis": read_json(project / "hypothesis.json"),
        "protocol": protocol, "inputs": fingerprints(project, paths),
    }


def current(project):
    key = metadata(project).get("active_protocol")
    require(isinstance(key, str) and bool(re.fullmatch(r"[0-9a-f]{64}", key)), "协议未冻结；先运行 freeze")
    stored = read_json(project / "protocols" / f"{key}.json")
    require(digest(stored.get("snapshot")) == key, "冻结协议内容校验失败")
    require(digest(snapshot(project)) == key, "协议/假设/预算/环境/切分/评测已改变；用 freeze --reason 建立新版本，旧结果不会混入")
    return key, stored["snapshot"]["protocol"]


def read_signed(path):
    data = read_json(path)
    expected = path.with_suffix(".sha256").read_text(encoding="ascii").strip()
    require(digest(data) == expected, f"记录已被改动: {path}")
    return data


def runs(project):
    result = []
    seen = set()
    for path in sorted((project / "runs").glob("*/record.json")):
        run = read_signed(path)
        require(run.get("id") == path.parent.name, f"run id 与目录不符: {path}")
        for entry in run.get("evidence", {}).values():
            require(file_hash(artifact(project, entry["path"])) == entry["sha256"], f"运行证据被改动: {entry['path']}")
        if run["kind"] == "confirmatory" and run["status"] == "completed":
            key = (run["protocol_sha256"], run["model_id"], run["dataset_id"], run["seed"])
            require(key not in seen, f"重复的正式实验单元: {key}")
            seen.add(key)
        result.append(run)
    return result


def budget_issues(project, records):
    budget = metadata(project)["budget"]
    issues = []
    if len(records) > budget["max_runs"]:
        issues.append("总运行数超过预算（包括失败、调试和旧协议运行）")
    hours = math.fsum(x["gpu_hours"] for x in records)
    if hours > budget["max_gpu_hours"] + 1e-12:
        issues.append(f"累计 GPU 小时 {hours:.6g} 超过预算 {budget['max_gpu_hours']}")
    if any(x["gpu_hours"] > budget["max_gpu_hours_per_run"] + 1e-12 for x in records):
        issues.append("存在超过单次 GPU 小时预算的运行")
    if "max_wall_hours" in budget and math.fsum(x["elapsed_seconds"] / 3600 for x in records) > budget["max_wall_hours"] + 1e-12:
        issues.append("累计运行墙钟小时超过预算（包括 CPU、失败及旧协议运行）")
    if "max_wall_hours_per_run" in budget and any(x["elapsed_seconds"] / 3600 > budget["max_wall_hours_per_run"] + 1e-12 for x in records):
        issues.append("存在超过单次墙钟小时预算的运行")
    return issues


def review_inputs(project, scope):
    paths = list(REVIEW_INPUTS[scope])
    key, protocol = current(project)
    kinds = ("smoke", "pilot") if scope == "pilot" else ("confirmatory",)
    baselines = {x["id"] for x in protocol["baselines"]}
    paths += [f"runs/{run['id']}/record.json" for run in runs(project)
              if run["protocol_sha256"] == key and run["kind"] in kinds
              and (scope != "pilot" or run["model_id"] in baselines)]
    if scope == "pilot":
        for entry in read_json(project / "pilot.json").get("checks", []):
            paths.extend(entry.get("artifacts", []))
    if scope == "paper":
        for entry in read_json(project / "claims.json").get("claims", []):
            if entry.get("included_in_paper") is True:
                paths.extend(entry.get("artifacts", []))
    return fingerprints(project, paths)


def review_reports(project, scope, protocol_key):
    reports = [read_signed(x) for x in (project / "reviews").glob("*/review.json")]
    return sorted((x for x in reports if x["scope"] == scope and x["protocol_sha256"] == protocol_key), key=lambda x: x["recorded_at"])


def validate_issues(project, issues):
    ids = []
    for issue in array(issues, "review.issues", nonempty=False):
        fields(issue, ("id", "description", "evidence"), "issue")
        ids.append(identifier(issue["id"], "issue.id"))
        require(issue.get("severity") in ("blocker", "major", "minor"), "issue.severity 无效")
        require(issue.get("status") in ("open", "resolved", "accepted"), "issue.status 无效")
        if issue["status"] != "open":
            fields(issue, ("resolution",), "issue")
            for path in array(issue.get("resolution_artifacts"), "issue.resolution_artifacts"):
                artifact(project, path)
        require(not (issue["severity"] == "blocker" and issue["status"] == "accepted"), "blocker 不能直接接受，需修复或缩小主张")
    require(len(ids) == len(set(ids)), "同一轮 review 的 issue.id 重复")


def merged_issues(project, reports):
    issues = {}
    for report in reports:
        validate_issues(project, report["issues"])
        for issue in report["issues"]:
            previous = issues.get(issue["id"])
            require(not previous or previous["severity"] == issue["severity"],
                    f"{issue['id']}: 历史问题不能通过改写严重级别关闭；保留级别，在 resolution 中说明修正判断及证据")
            issues[issue["id"]] = issue
    return issues


def check_review(project, scope):
    key, _ = current(project)
    reports = review_reports(project, scope, key)
    require(reports, f"缺少 {scope} 审查；使用 review 登记审查结果")
    for report in reports:
        for path, expected in report.get("resolution_evidence", {}).items():
            require(file_hash(artifact(project, path)) == expected, f"审查修复证据已变更: {path}")
    require(reports[-1]["reviewed_artifacts"] == review_inputs(project, scope), f"{scope} 审查已过期；文件或运行集合发生变化，需要复审")
    issues = merged_issues(project, reports)
    blockers = [x["id"] for x in issues.values() if x["severity"] in ("blocker", "major") and x["status"] == "open"]
    require(not blockers, f"{scope} 尚未关闭的重要问题: {', '.join(blockers)}")


def check_protocol(project):
    current(project)


def check_pilot(project):
    key, protocol = current(project)
    report = read_json(project / "pilot.json")
    require(report.get("protocol_sha256") == key, "pilot.json 未绑定当前协议")
    checks = array(report.get("checks"), "pilot.checks")
    names = [x.get("name") for x in checks]
    require(len(names) == len(set(names)) and set(PILOT_CHECKS) <= set(names), "pilot.checks 缺少必要检查或名称重复")
    for check in checks:
        require(check.get("status") in ("pass", "na"), f"pilot.{check.get('name')}: 尚未通过")
        if check.get("name") == "evaluator_sensitivity":
            require(check.get("status") == "pass", "pilot.evaluator_sensitivity: 需实际验证评测能区分预设对照，不能用 na 跳过")
        fields(check, ("reason",), "pilot.check")
        for path in array(check.get("artifacts"), "pilot.check.artifacts"):
            artifact(project, path)
    records = runs(project)
    require(not budget_issues(project, records), "; ".join(budget_issues(project, records)))
    for baseline in protocol["baselines"]:
        for dataset in protocol["datasets"]:
            require(any(x["protocol_sha256"] == key and x["kind"] == "pilot" and x["status"] == "completed"
                        and x["model_id"] == baseline["id"] and x["dataset_id"] == dataset["id"] for x in records),
                    f"{baseline['id']}/{dataset['id']}: 缺少有证据的 pilot 运行")
    check_review(project, "pilot")


def summary(project):
    key, protocol = current(project)
    records = runs(project)
    selected = [x for x in records if x["protocol_sha256"] == key and x["kind"] == "confirmatory" and x["status"] == "completed"]
    grid = set(itertools.product((x["id"] for x in models(protocol)), (x["id"] for x in protocol["datasets"]), protocol["seeds"]))
    groups = {}
    for run in selected:
        cell = (run["model_id"], run["dataset_id"], run["seed"])
        require(cell in grid, f"{run['id']}: 正式运行不在预注册实验网格内")
        grid.remove(cell)
        groups.setdefault(cell[:2], []).append(run)
    rows = []
    for (model, dataset), group in sorted(groups.items()):
        values = [x["metrics"][protocol["primary_metric"]["name"]] for x in group]
        rows.append({"model": model, "dataset": dataset, "n": len(values), "mean": statistics.fmean(values),
                     "sample_std": statistics.stdev(values) if len(values) > 1 else None,
                     "seeds": sorted(x["seed"] for x in group), "run_ids": sorted(x["id"] for x in group)})
    return {"protocol_sha256": key, "metric": protocol["primary_metric"], "rows": rows,
            "missing": [list(x) for x in sorted(grid)], "run_ids": sorted(x["id"] for x in selected),
            "budget_issues": budget_issues(project, records)}


def check_experiments(project):
    expected = summary(project)
    require(not expected["missing"], f"正式实验网格不完整，还缺 {len(expected['missing'])} 个单元；smoke/pilot 不计入")
    require(not expected["budget_issues"], "; ".join(expected["budget_issues"]))
    require(read_json(project / "reports/summary.json") == expected, "汇总缺失或过期；重新运行 summarize")
    artifact(project, "reports/analysis.md")
    require(string((project / "reports/analysis.md").read_text(encoding="utf-8")), "analysis.md 仍有占位符")
    check_review(project, "experiments")


def check_paper(project):
    key, protocol = current(project)
    valid_runs = {x["id"]: x for x in runs(project) if x["protocol_sha256"] == key and x["kind"] == "confirmatory" and x["status"] == "completed"}
    papers = {x["id"]: x for x in read_json(project / "literature.json")["papers"]}
    data = read_json(project / "claims.json")
    claims = array(data.get("claims"), "claims")
    included = [x for x in claims if x.get("included_in_paper") is True]
    require(included, "没有纳入论文且有证据的主张")
    ids = []
    for claim in claims:
        ids.append(identifier(claim.get("id"), "claim.id"))
        require(type(claim.get("included_in_paper")) is bool, "claim.included_in_paper 必须为布尔值")
    require(len(ids) == len(set(ids)), "claim.id 重复")
    for claim in included:
        fields(claim, ("text", "scope", "limitation", "location"), "claim")
        require(claim.get("status") in ("supported", "qualified"), f"{claim['id']}: 未获证据支持的主张仍在文稿中")
        require(claim.get("kind") in ("empirical", "mechanistic", "literature"), "claim.kind 无效")
        for path in array(claim.get("artifacts"), "claim.artifacts"):
            artifact(project, path)
        cited_runs = array(claim.get("run_ids"), "claim.run_ids", nonempty=claim["kind"] != "literature")
        require(all(isinstance(x, str) and x in valid_runs for x in cited_runs), "主张引用了不属于当前正式实验的运行")
        cited_papers = array(claim.get("paper_ids"), "claim.paper_ids", nonempty=claim["kind"] == "literature")
        require(all(isinstance(x, str) and x in papers for x in cited_papers), "主张引用了未登记的论文")
        if claim["kind"] == "mechanistic":
            ablations = {x["id"] for x in protocol["ablations"]}
            require(any(valid_runs[x]["model_id"] in ablations for x in cited_runs), "机制主张需要相应消融运行；因果解释仍需人工审查")
    manuscript = artifact(project, "paper/manuscript.md").read_text(encoding="utf-8")
    require(string(manuscript), "manuscript.md 仍有 {{...}} 占位符")
    bibliography = artifact(project, "paper/references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bibliography))
    citations = set(re.findall(r"\[@([A-Za-z0-9_.:-]+)\]", manuscript))
    require(citations and citations <= set(papers) and citations <= keys, "正文引用必须使用 [@P001]，并对应 literature 与 references.bib 的相同 key")
    check_review(project, "paper")


def check_submission(project):
    data = read_json(project / "submission.json")
    fields(data, ("venue", "year", "track", "policy_url", "checked_at", "pdf"), "submission")
    require(data["policy_url"].startswith("https://"), "提交规范需要官方 HTTPS 来源")
    require(artifact(project, data["pdf"]).read_bytes().startswith(b"%PDF-"), "提交稿缺少 PDF 文件头")
    checks = data.get("checks")
    require(isinstance(checks, dict), "submission.checks 必须为对象")
    for name in SUBMISSION_CHECKS:
        check = checks.get(name)
        fields(check, ("reason",), f"submission.{name}")
        require(check.get("status") in ("pass", "na"), f"submission.{name}: 尚未通过")
        for path in array(check.get("artifacts"), f"submission.{name}.artifacts"):
            artifact(project, path)
    for path in array(data.get("package_files"), "submission.package_files"):
        artifact(project, path)


CHECKS = (check_scope, check_literature, check_hypothesis, check_protocol, check_pilot, check_experiments, check_paper, check_submission)


def check(project, through):
    issues = []
    for stage, function in zip(STAGES, CHECKS):
        try:
            function(project)
        except (Problem, OSError, KeyError, TypeError, AttributeError, ValueError) as exc:
            issues.append(f"{stage}: {exc}")
        if stage == through:
            break
    return issues


def require_checks(project, through):
    issues = check(project, through)
    require(not issues, "\n".join(issues))


def save_signed(directory, name, data):
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / name, data)
    (directory / Path(name).with_suffix(".sha256")).write_text(digest(data) + "\n", encoding="ascii")


def init_project(args):
    target = args.project.resolve()
    require((ROOT / "templates/workspace").is_dir(), "init 请使用框架仓库中的 scripts/research.py；工作目录内 tools/research.py 用于继续现有研究")
    require(not target.exists(), f"目标已存在，未覆盖: {target}")
    require(string(args.topic), "topic 不能为空")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".research-init-", dir=target.parent))
    try:
        shutil.copytree(ROOT / "templates/workspace", temporary, dirs_exist_ok=True)
        shutil.copytree(ROOT / "skills", temporary / ".agents/skills")
        for source in (ROOT / "scripts").glob("*.py"):
            shutil.copy2(source, temporary / "tools" / source.name)
        data = read_json(temporary / "project.json")
        data.update(topic=args.topic, created_at=now(), stage="scope", active_protocol=None)
        write_json(temporary / "project.json", data)
        os.rename(temporary, target)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    print(f"已创建 {target}\nAgent 入口: {target / 'AGENTS.md'}\n本地工具: python3 tools/research.py status --project .")


def freeze(args):
    project = args.project.resolve()
    require_checks(project, "hypothesis")
    data = metadata(project)
    contract = snapshot(project)
    key = digest(contract)
    previous = data.get("active_protocol")
    if previous == key:
        current(project)
        print(f"协议已冻结: {key}")
        return
    require(not previous or string(args.reason), "修改已冻结协议需要 --reason，说明修改原因和旧结果的处理")
    path = project / "protocols" / f"{key}.json"
    require(not path.exists(), "此协议版本已有历史记录；请明确修订协议，避免复用旧实验造成混淆")
    write_json(path, {"sha256": key, "created_at": now(), "previous": previous, "reason": args.reason or "首次冻结", "snapshot": contract})
    data.update(active_protocol=key, stage="pilot")
    write_json(project / "project.json", data)
    with (project / "DECISIONS.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\n- {now()} 冻结协议 `{key}`；原因：{args.reason or '首次冻结'}；阶段：pilot。\n")
    print(f"协议已冻结，进入 pilot: {key}\n正式实验必须显式使用此 protocol_sha256。")


def record(args):
    project = args.project.resolve()
    key, protocol = current(project)
    data = read_json(args.file)
    run_id = identifier(data.get("id"), "run.id")
    require(not (project / "runs" / run_id).exists(), f"运行 id 已存在: {run_id}")
    require(data.get("protocol_sha256") == key, "输入运行没有绑定当前冻结协议")
    require(data.get("kind") in ("smoke", "pilot", "confirmatory"), "run.kind 无效")
    require(data.get("status") in ("completed", "failed"), "run.status 无效")
    split = data.get("evaluation_split", "unknown")
    require(split in ("train", "validation", "test", "unknown"), "run.evaluation_split 无效")
    if data["kind"] in ("smoke", "pilot"):
        require(split != "test", "探索和调试不得用 test 选择方法；已发生的测试暴露需另写污染记录并修订确认计划")
    require(data.get("model_id") in {x["id"] for x in models(protocol)}, "run.model_id 未在协议中登记")
    require(data.get("dataset_id") in {x["id"] for x in protocol["datasets"]}, "run.dataset_id 未在协议中登记")
    require(type(data.get("seed")) is int and data["seed"] in protocol["seeds"], "run.seed 未在协议中登记")
    fields(data, ("command", "code_revision", "code_artifact", "environment_file", "log_file"), "run")
    seconds = number(data.get("elapsed_seconds"), "run.elapsed_seconds")
    gpu_count = data.get("gpu_count")
    require(type(gpu_count) is int and gpu_count >= 0, "run.gpu_count 需要非负整数")
    require(seconds > 0, "实际运行 elapsed_seconds 需要 > 0")
    records = runs(project)
    if data["kind"] == "confirmatory" and data["status"] == "completed":
        require(not any(x["protocol_sha256"] == key and x["kind"] == "confirmatory" and x["status"] == "completed" and all(x[k] == data[k] for k in ("model_id", "dataset_id", "seed")) for x in records), "正式实验单元重复；调参应登记为 pilot，失败记录可保留后重试")
    source_names = {"code": data["code_artifact"], "environment": data["environment_file"], "log": data["log_file"]}
    if "config_file" in data:
        fields(data, ("config_file",), "run")
        source_names["config"] = data["config_file"]
    if "intent_file" in data:
        fields(data, ("intent_file",), "run")
        source_names["intent"] = data["intent_file"]
    metrics = {}
    if data["status"] == "completed":
        fields(data, ("metrics_file",), "run")
        source_names["metrics"] = data["metrics_file"]
        metrics = read_json(artifact(project, data["metrics_file"]))
        require(bool(metrics), "metrics 文件不能为空")
        if data["kind"] != "smoke":
            require(protocol["primary_metric"]["name"] in metrics, "metrics 文件缺少主要指标")
        for name, value in metrics.items():
            number(value, f"metric.{name}", minimum=-sys.float_info.max)
    else:
        fields(data, ("failure_reason",), "run")
    sources = {name: artifact(project, path) for name, path in source_names.items()}
    frozen = read_json(project / "protocols" / f"{key}.json")["snapshot"]
    require(file_hash(sources["environment"]) == frozen["inputs"][protocol["environment_file"]], "运行环境与冻结环境不一致；先修订协议")
    record_data = {k: data[k] for k in ("id", "protocol_sha256", "kind", "status", "model_id", "dataset_id", "seed", "command", "code_revision", "elapsed_seconds", "gpu_count")}
    record_data.update(recorded_at=now(), gpu_hours=seconds * gpu_count / 3600, metrics=metrics,
                       evaluation_split=split, notes=data.get("notes", ""), failure_reason=data.get("failure_reason", ""), evidence={})
    directory = project / "runs"
    directory.mkdir(exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".pending-", dir=directory))
    try:
        for name, source in sources.items():
            destination = temporary / f"{name}{source.suffix}"
            shutil.copy2(source, destination)
            record_data["evidence"][name] = {"path": f"runs/{run_id}/{destination.name}", "sha256": file_hash(destination)}
        require(record_data["evidence"]["environment"]["sha256"] == frozen["inputs"][protocol["environment_file"]], "环境在登记过程中改变，未保存该运行；请核查实际环境")
        if data["status"] == "completed":
            archived_metrics = temporary / Path(record_data["evidence"]["metrics"]["path"]).name
            require(read_json(archived_metrics) == metrics, "指标在登记过程中改变，未保存该运行；请等待结果写完后重试")
        save_signed(temporary, "record.json", record_data)
        os.rename(temporary, directory / run_id)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    print(f"已登记 {run_id}（{data['kind']}/{data['status']}），证据已复制并校验。")
    issues = budget_issues(project, records + [record_data])
    if issues:
        print("预算超限，记录仍保留，阶段检查将失败：" + "; ".join(issues), file=sys.stderr)
        return 1
    return 0


def register_review(args):
    project = args.project.resolve()
    key, _ = current(project)
    data = read_json(args.file)
    review_id = identifier(data.get("id"), "review.id")
    require(data.get("scope") in REVIEW_INPUTS, "review.scope 必须为 pilot / experiments / paper")
    require(data.get("protocol_sha256") == key, "审查未绑定当前协议")
    fields(data, ("reviewer", "assessment"), "review")
    validate_issues(project, data.get("issues"))
    path = project / "reviews" / review_id
    require(not path.exists(), f"审查 id 已存在: {review_id}")
    report = {k: data[k] for k in ("id", "scope", "protocol_sha256", "reviewer", "assessment", "issues")}
    merged_issues(project, review_reports(project, data["scope"], key) + [report])
    report.update(recorded_at=now(), reviewed_artifacts=review_inputs(project, data["scope"]))
    report["resolution_evidence"] = fingerprints(project, [path for issue in data["issues"]
                                                         for path in issue.get("resolution_artifacts", [])])
    (project / "reviews").mkdir(exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".pending-", dir=project / "reviews"))
    try:
        save_signed(temporary, "review.json", report)
        os.rename(temporary, path)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    print(f"已登记审查 {review_id}。同协议同阶段的旧问题会继续累计，不能通过省略旧问题关闭它们。")


def summarize(args):
    project = args.project.resolve()
    data = summary(project)
    write_json(project / "reports/summary.json", data)
    lines = [f"# 正式实验汇总：{data['metric']['name']}（{data['metric']['direction']}）", "", f"协议：`{data['protocol_sha256']}`", "", "| 模型 | 数据集 | n | mean | sample std |", "| --- | --- | ---: | ---: | ---: |"]
    for row in data["rows"]:
        std = f"{row['sample_std']:.8g}" if row["sample_std"] is not None else "N/A (n=1)"
        lines.append(f"| {row['model']} | {row['dataset']} | {row['n']} | {row['mean']:.8g} | {std} |")
    lines += ["", f"缺少实验单元：{len(data['missing'])}。", "", "std 是运行间样本标准差，不是置信区间或显著性检验。调试与 pilot 不计入。"]
    (project / "reports/summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成 reports/summary.json 和 summary.md；还缺 {len(data['missing'])} 个正式单元。")


def propose(args):
    """Save a falsifiable proposal only after the baseline environment has been reviewed."""
    project = args.project.resolve()
    require_checks(project, "pilot")
    data = read_json(args.file)
    idea_id = identifier(data.get("id"), "idea.id")
    identifier(data.get("model_id"), "idea.model_id")
    fields(data, ("title", "failure", "mechanism", "intervention", "prediction", "falsifier", "novelty"), "idea")
    require(all(string(x) for x in array(data.get("alternatives"), "idea.alternatives")), "需要明确替代解释")
    papers = {p["id"] for p in read_json(project / "literature.json")["papers"]}
    related = array(data.get("paper_ids"), "idea.paper_ids")
    require(all(isinstance(x, str) and x in papers for x in related), "创新对照需要真实登记的近邻文献")
    fields(data.get("minimal_test"), ("comparison", "readout", "support_if", "stop_if", "cost"), "idea.minimal_test")
    evidence = fingerprints(project, array(data.get("artifacts"), "idea.artifacts"))
    destination = project / "ideas" / idea_id
    require(not destination.exists(), f"idea 已存在: {idea_id}；修订请保留旧提案，建立新 id")
    data.update(created_at=now(), foundation_protocol=current(project)[0], evidence=evidence)
    save_signed(destination, "proposal.json", data)
    print(f"已登记 {idea_id}；先做 minimal_test，再决定是否扩大实验。")


def decide(args):
    """Record an evidence-backed continue/revise/drop/promote decision, including negative results."""
    project = args.project.resolve()
    data = read_json(args.file)
    decision_id = identifier(data.get("id"), "decision.id")
    idea_id = identifier(data.get("idea_id"), "decision.idea_id")
    proposal = read_signed(project / "ideas" / idea_id / "proposal.json")
    for path, expected in proposal["evidence"].items():
        require(file_hash(artifact(project, path)) == expected, f"提案依据已变更: {path}")
    require(data.get("action") in ("continue", "revise", "drop", "promote"), "decision.action 无效")
    fields(data, ("interpretation", "alternative_explanations", "next_test"), "decision")
    records = {x["id"]: x for x in runs(project)}
    cited = array(data.get("run_ids"), "decision.run_ids")
    require(all(isinstance(x, str) and x in records for x in cited), "决策引用了未登记运行")
    selected = [records[x] for x in cited]
    require(any(x["model_id"] == proposal["model_id"] for x in selected), "决策必须包含该候选的真实运行（也可为失败）")
    if data["action"] == "promote":
        require_checks(project, "pilot")
        key, protocol = current(project)
        eligible = [x for x in selected if x["kind"] == "pilot" and x["status"] == "completed"
                    and x["protocol_sha256"] == key and x.get("evaluation_split") == "validation"]
        required = {proposal["model_id"], *(b["id"] for b in protocol["baselines"])}
        require(required <= {x["model_id"] for x in eligible}, "晋级需当前协议下候选和各基线的 validation pilot；五秒 smoke、旧协议或未知切分不能晋级")
        cells = [{(x["dataset_id"], x["seed"]) for x in eligible if x["model_id"] == model} for model in required]
        require(set.intersection(*cells), "晋级比较需候选和各基线共享至少一个数据集/种子单元，不能跨任务拼出优势")
        fields(data, ("confirmation_plan",), "decision")
    evidence = fingerprints(project, array(data.get("artifacts"), "decision.artifacts"))
    destination = project / "ideas" / idea_id / "decisions" / decision_id
    require(not destination.exists(), f"决策 id 已存在: {decision_id}")
    data.update(recorded_at=now(), evidence=evidence)
    save_signed(destination, "decision.json", data)
    with (project / "DECISIONS.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\n- {now()} `{idea_id}` → {data['action']}：{data['interpretation']}；证据：{', '.join(cited)}；下一步：{data['next_test']}。\n")
    print(f"已保存 {idea_id}/{decision_id}: {data['action']}。晋级仅表示值得正式验证。")


def next_actions(project):
    data = metadata(project)
    issues = check(project, data["stage"])
    records = runs(project)
    ideas = []
    for path in sorted((project / "ideas").glob("*/proposal.json")):
        idea = read_signed(path)
        decisions = sorted((read_signed(p) for p in path.parent.glob("decisions/*/decision.json")), key=lambda x: x["recorded_at"])
        for item in [idea] + decisions:
            for name, expected in item["evidence"].items():
                require(file_hash(artifact(project, name)) == expected, f"提案或决策依据已变更: {name}")
        last = decisions[-1] if decisions else None
        ideas.append({"id": idea["id"], "title": idea["title"], "action": last["action"] if last else "test",
                      "next_test": last["next_test"] if last else idea["minimal_test"]})
    return {"stage": data["stage"], "issues": issues, "ideas": ideas,
            "used": {"runs": len(records), "gpu_hours": math.fsum(x["gpu_hours"] for x in records),
                     "wall_hours": math.fsum(x["elapsed_seconds"] / 3600 for x in records)},
            "budget": data["budget"],
            "next": "先处理当前阶段缺项" if issues else ("读取候选最小实验及最近决策，执行下一项可判别实验；无候选则根据失效证据 propose" if data["stage"] in ("pilot", "experiments") else "运行 advance 或继续当前阶段交付")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("init", "status", "check", "advance", "freeze", "record", "summarize", "review", "execute", "propose", "decide", "next"):
        sub = commands.add_parser(name)
        sub.add_argument("--project", type=Path, required=True, help="科研工作目录")
        if name == "init":
            sub.add_argument("--topic", required=True)
        if name in ("record", "review", "execute", "propose", "decide"):
            sub.add_argument("--file", type=Path, required=True)
        if name == "execute":
            sub.add_argument("--dry-run", action="store_true", help="检查命令、预算和阶段，不启动进程")
        if name == "freeze":
            sub.add_argument("--reason")
        if name == "check":
            sub.add_argument("--stage", choices=STAGES, help="累计检查至该阶段，默认当前阶段")
        if name in ("status", "check"):
            sub.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        args.project = args.project.resolve()
        if args.action == "init":
            init_project(args)
        elif args.action == "freeze":
            freeze(args)
        elif args.action == "record":
            return record(args)
        elif args.action == "review":
            register_review(args)
        elif args.action == "summarize":
            summarize(args)
        elif args.action == "propose":
            propose(args)
        elif args.action == "decide":
            decide(args)
        elif args.action == "next":
            print(json.dumps(next_actions(args.project), ensure_ascii=False, indent=2))
        elif args.action == "execute":
            import experiment_runner
            return experiment_runner.execute(args, sys.modules[__name__])
        elif args.action in ("status", "check"):
            data = metadata(args.project)
            stage = getattr(args, "stage", None) or data["stage"]
            issues = check(args.project, stage)
            output = {"topic": data["topic"], "stage": data["stage"], "checked_through": stage, "active_protocol": data.get("active_protocol"), "passed": not issues, "issues": issues}
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print(f"{data['topic']} | 当前阶段: {data['stage']} | 检查至: {stage}")
                print("\n".join(f"- {x}" for x in issues) if issues else "本地证据检查通过；科学有效性和投稿适配仍需判断。")
            return int(bool(issues)) if args.action == "check" else 0
        elif args.action == "advance":
            data = metadata(args.project)
            require_checks(args.project, data["stage"])
            position = STAGES.index(data["stage"])
            require(position + 1 < len(STAGES), "已到投稿准备阶段；本工具不执行提交")
            data["stage"] = STAGES[position + 1]
            write_json(args.project / "project.json", data)
            print(f"进入 {data['stage']}")
        return 0
    except (Problem, OSError, KeyError, TypeError, AttributeError, ValueError, OverflowError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
