"""Actual tiny subprocesses in temporary fixtures; never scientific evidence."""

import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_research as fixtures

rf, ROOT = fixtures.rf, fixtures.ROOT


spec = importlib.util.spec_from_file_location("runner", ROOT / "scripts/experiment_runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ExecutionTests(unittest.TestCase):
    setUp = fixtures.ResearchTests.setUp
    quiet = fixtures.ResearchTests.quiet
    put = fixtures.ResearchTests.put
    run_input = fixtures.ResearchTests.run_input
    add_run = fixtures.ResearchTests.add_run
    add_review = fixtures.ResearchTests.add_review
    pilot = fixtures.ResearchTests.pilot

    def job(self, name="EXEC", model="B", code=None, **changes):
        code = code or "import json,os; from pathlib import Path; Path(os.environ['RESEARCH_OUTPUT_DIR'],'metrics.json').write_text(json.dumps({'loss':sum(i*i for i in range(8))}))"
        script = f"artifacts/{name}.py"
        self.put(script, code)
        job = dict(id=name, protocol_sha256=rf.current(self.project)[0], kind="pilot", model_id=model,
                   dataset_id="D", seed=1, argv=[sys.executable, script], evaluation_split="validation",
                   gpu_count=0, timeout_seconds=5, code_revision="temporary subprocess fixture",
                   code_artifact=script, environment_file="artifacts/environment.txt")
        job.update(changes)
        return job

    def execute(self, job, dry_run=False):
        source = self.project / "artifacts/job-input.json"
        rf.write_json(source, job)
        return self.quiet(runner.execute, argparse.Namespace(project=self.project, file=source, dry_run=dry_run), rf)

    def test_success_creates_real_logs_metrics_and_measured_cost(self):
        job = self.job()
        self.assertEqual(self.execute(job, dry_run=True), 0)
        self.assertFalse((self.project / "executions").exists())
        self.assertEqual(self.execute(job), 0)
        run = rf.runs(self.project)[0]
        self.assertEqual(run["metrics"]["loss"], sum(i * i for i in range(8)))
        self.assertGreater(run["elapsed_seconds"], 0)
        self.assertEqual(run["evaluation_split"], "validation")
        self.assertFalse((self.project / ".execution.lock").exists())

    def test_failure_stops_plan_and_keeps_failed_cost(self):
        first = self.job("FAIL", code="raise SystemExit(7)")
        second = self.job("NEVER")
        self.assertEqual(self.execute({"jobs": [first, second]}), 1)
        self.assertEqual([x["id"] for x in rf.runs(self.project)], ["FAIL"])
        self.assertEqual(rf.runs(self.project)[0]["status"], "failed")
        self.assertIn("7", rf.runs(self.project)[0]["failure_reason"])
        self.assertFalse((self.project / "executions/NEVER").exists())

    def test_prediction_is_archived_before_training_changes_working_copy(self):
        self.put("artifacts/intent.md", "BEFORE: fixture prediction\n")
        code = "import os,json\nfrom pathlib import Path\nPath('artifacts/intent.md').write_text('AFTER: changed during fixture execution\\n')\nPath(os.environ['RESEARCH_OUTPUT_DIR'],'metrics.json').write_text(json.dumps({'loss':sum(range(3))}))"
        self.assertEqual(self.execute(self.job(code=code, intent_file="artifacts/intent.md")), 0)
        evidence = rf.runs(self.project)[0]["evidence"]["intent"]
        self.assertEqual((self.project / evidence["path"]).read_text(), "BEFORE: fixture prediction\n")
        self.assertIn("AFTER", (self.project / "artifacts/intent.md").read_text())
        (self.project / evidence["path"]).write_text("Edited archived prediction\n")
        with self.assertRaises(rf.Problem):
            rf.runs(self.project)

    def test_missing_prediction_file_stops_before_launch(self):
        with self.assertRaisesRegex(rf.Problem, "证据文件不存在"):
            self.execute(self.job(intent_file="artifacts/missing-intent.md"))
        self.assertFalse((self.project / "executions/EXEC").exists())

    def test_timeout_terminates_descendants(self):
        code = "import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c',\"import time;from pathlib import Path;time.sleep(0.5);Path('escaped-child.txt').write_text('bad')\"])\ntime.sleep(10)"
        self.assertEqual(self.execute(self.job(code=code, timeout_seconds=0.15)), 1)
        # A second actual process provides enough elapsed time to catch a leaked child.
        subprocess.run([sys.executable, "-c", "import time;time.sleep(0.6)"], check=True)
        self.assertFalse((self.project / "escaped-child.txt").exists())
        self.assertIn("timeout_seconds", rf.runs(self.project)[0]["failure_reason"])

    def test_missing_or_invalid_metrics_is_recorded_as_failure(self):
        for name, code in (("MISSING", "pass"), ("NAN", "import os;from pathlib import Path;Path(os.environ['RESEARCH_OUTPUT_DIR'],'metrics.json').write_text('{\"loss\": NaN}')")):
            self.assertEqual(self.execute(self.job(name, code=code)), 1)
        self.assertTrue(all(x["status"] == "failed" for x in rf.runs(self.project)))

    def test_smoke_can_check_correctness_without_benchmark_score(self):
        code = "import os,json;from pathlib import Path;assert sum([1,2,3])==6;Path(os.environ['RESEARCH_OUTPUT_DIR'],'metrics.json').write_text(json.dumps({'checks_passed':1}))"
        self.assertEqual(self.execute(self.job(code=code, kind="smoke", evaluation_split="train")), 0)
        self.assertEqual(rf.runs(self.project)[0]["metrics"], {"checks_passed": 1})
        self.assertEqual(rf.summary(self.project)["rows"], [])

    def test_gpu_and_cpu_budget_reject_before_start(self):
        with self.assertRaisesRegex(rf.Problem, "预算"):
            self.execute(self.job(gpu_count=1))
        with self.assertRaisesRegex(rf.Problem, "预算"):
            self.execute(self.job(timeout_seconds=10000))
        self.assertFalse((self.project / "executions").exists())

    def test_candidate_waits_for_reviewed_foundation_then_does_not_stale_it(self):
        with self.assertRaisesRegex(rf.Problem, "pilot"):
            self.execute(self.job(model="C"))
        self.pilot()
        self.assertEqual(self.execute(self.job(model="C")), 0)
        rf.check_review(self.project, "pilot")

    def test_test_set_cannot_be_used_for_pilot(self):
        with self.assertRaisesRegex(rf.Problem, "evaluation_split"):
            self.execute(self.job(evaluation_split="test"))

    def test_incomplete_previous_execution_is_not_free_retry(self):
        self.put("executions/CRASH/stdout.log", "Previous process crashed before registration")
        with self.assertRaisesRegex(rf.Problem, "未登记"):
            self.execute(self.job())

    def test_formal_execution_requires_frozen_source_config_and_model_pilot(self):
        job = self.job(kind="confirmatory", evaluation_split="test")
        self.pilot()
        with self.assertRaisesRegex(rf.Problem, "code_artifact"):
            self.execute(job)
        protocol = rf.read_json(self.project / "protocol.json")
        self.put("artifacts/config.json", '{"fixture":true}')
        protocol["baselines"][0].update(code_artifact=job["code_artifact"], config_file="artifacts/config.json")
        rf.write_json(self.project / "protocol.json", protocol)
        self.args.reason = "Freeze real fixture executable"
        self.quiet(rf.freeze, self.args)
        self.add_run("PILOT-NEW", kind="pilot")
        pilot = rf.read_json(self.project / "pilot.json")
        pilot["protocol_sha256"] = rf.current(self.project)[0]
        rf.write_json(self.project / "pilot.json", pilot)
        self.add_review("RV-new", "pilot")
        job["protocol_sha256"] = rf.current(self.project)[0]
        self.assertEqual(self.execute(job), 0)
        completed = next(x for x in rf.runs(self.project) if x["id"] == job["id"])
        self.assertIn("config", completed["evidence"])
        with self.assertRaises(rf.Problem):
            self.execute({**job, "id": "SECOND"})

    def test_copied_cli_executes_from_generated_workspace(self):
        job = self.job()
        source = self.project / "artifacts/cli-job.json"
        rf.write_json(source, job)
        output = subprocess.run([sys.executable, str(self.project / "tools/research.py"), "execute", "--project", str(self.project), "--file", str(source)], capture_output=True, text=True)
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(len(rf.runs(self.project)), 1)

    def proposal(self):
        self.pilot()
        data = dict(id="I1", model_id="C", title="Fixture hypothesis", failure="fixture failure",
                    mechanism="fixture mechanism", intervention="fixture intervention", prediction="fixture prediction",
                    falsifier="fixture falsifier", novelty="No genuine novelty asserted in tests", alternatives=["fixture"],
                    paper_ids=["P_TEST"], artifacts=["artifacts/pilot.txt"],
                    minimal_test=dict(comparison="B versus C", readout="loss", support_if="fixture", stop_if="fixture", cost="CPU only"))
        path = self.project / "artifacts/proposal-input.json"
        rf.write_json(path, data)
        self.quiet(rf.propose, argparse.Namespace(project=self.project, file=path))

    def decision(self, action, run_ids):
        data = dict(id="DEC1", idea_id="I1", action=action, interpretation="Fixture outcome",
                    alternative_explanations="Fixture confound", next_test="Fixture next step", run_ids=run_ids,
                    artifacts=["artifacts/pilot.txt"], confirmation_plan="Fresh held-out fixture evaluation")
        path = self.project / "artifacts/decision-input.json"
        rf.write_json(path, data)
        return self.quiet(rf.decide, argparse.Namespace(project=self.project, file=path))

    def test_smoke_only_cannot_promote_idea(self):
        self.proposal()
        self.assertEqual(self.execute(self.job("SHORT", model="C", kind="smoke")), 0)
        with self.assertRaisesRegex(rf.Problem, "晋级需"):
            self.decision("promote", ["PILOT", "SHORT"])

    def test_validation_comparison_promotes_but_does_not_claim_success(self):
        self.proposal()
        self.assertEqual(self.execute(self.job("BASE")), 0)
        self.add_review("RV-base-updated", "pilot")
        self.assertEqual(self.execute(self.job("CAND", model="C")), 0)
        self.decision("promote", ["BASE", "CAND"])
        status = rf.next_actions(self.project)
        self.assertEqual(status["ideas"][0]["action"], "promote")
        self.assertFalse(rf.summary(self.project)["rows"])

    def test_failed_candidate_can_be_dropped_and_cost_remains(self):
        self.proposal()
        self.assertEqual(self.execute(self.job("BAD", model="C", code="raise SystemExit(1)")), 1)
        self.decision("drop", ["BAD"])
        self.assertEqual(rf.next_actions(self.project)["ideas"][0]["action"], "drop")
        self.assertEqual(rf.next_actions(self.project)["used"]["runs"], 2)

    def test_decision_evidence_cannot_silently_change(self):
        self.proposal()
        self.assertEqual(self.execute(self.job("CAND", model="C")), 0)
        self.decision("continue", ["CAND"])
        self.put("artifacts/pilot.txt", "A rewritten explanation")
        with self.assertRaisesRegex(rf.Problem, "依据已变更"):
            rf.next_actions(self.project)

    def test_unmatched_pilot_seeds_cannot_promote(self):
        self.proposal()
        self.assertEqual(self.execute(self.job("BASE", seed=1)), 0)
        self.add_review("RV-base-new", "pilot")
        self.assertEqual(self.execute(self.job("CAND", model="C", seed=2)), 0)
        with self.assertRaisesRegex(rf.Problem, "共享"):
            self.decision("promote", ["BASE", "CAND"])

    def test_foundation_protocol_does_not_require_invented_candidate(self):
        protocol = rf.read_json(self.project / "protocol.json")
        protocol.update(candidates=[], ablations=[])
        rf.write_json(self.project / "protocol.json", protocol)
        self.args.reason = "Foundation only"
        self.quiet(rf.freeze, self.args)
        self.assertEqual(self.execute(self.job()), 0)


if __name__ == "__main__":
    unittest.main()
