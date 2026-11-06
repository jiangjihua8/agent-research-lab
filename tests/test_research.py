"""Synthetic fixtures only: exercise evidence invariants, never assert real research."""

import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("research", ROOT / "scripts/research.py")
rf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rf)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name) / "study"
        with contextlib.redirect_stdout(io.StringIO()):
            rf.init_project(argparse.Namespace(project=self.project, topic="TEST FIXTURE, NOT A RESEARCH RESULT"))
        self.args = argparse.Namespace(project=self.project, reason=None)
        data = rf.metadata(self.project)
        data.update(research_question="Fixture question", contribution="Fixture comparison", constraints="CPU fixtures only")
        rf.write_json(self.project / "project.json", data)
        rf.write_json(self.project / "literature.json", {
            "synthesis": "Unit-test fixture, not a genuine literature review",
            "searches": [{"query": "fixture", "source": "mock source", "searched_at": "2026-11-05"}],
            "papers": [{"id": "P_TEST", "title": "MOCK PAPER FOR UNIT TEST ONLY", "url": "https://example.org/fixture", "problem": "fixture", "mechanism": "fixture", "evidence": "fixture", "limitations": "fixture", "accessed_at": "2026-11-05", "source_checked": True, "relevance": "direct", "read_status": "full"}],
        })
        rf.write_json(self.project / "hypothesis.json", {
            "baseline_failure": "fixture", "explanation": "fixture", "intervention": "fixture",
            "predictions": ["fixture"], "falsification": "fixture", "alternatives": ["fixture"],
            "related_work_ids": ["P_TEST"], "novelty": "not asserted", "evidence_cost": "fixture",
        })
        self.put("artifacts/environment.txt", "Fixture Python environment\n")
        self.put("artifacts/evaluate.py", "# A fixture, not a research implementation\n")
        self.put("artifacts/splits.json", '{"train":[1],"validation":[2],"test":[3]}')
        self.put("artifacts/code.py", "# Complete fixture code\n")
        self.put("artifacts/pilot.txt", "A synthetic test artifact only\n")
        protocol = rf.read_json(self.project / "protocol.json")
        protocol.update(primary_metric={"name": "loss", "direction": "min"}, seeds=[1, 2],
                        uncertainty="Fixture seed variability", datasets=[{"id": "D", "version": "fixture-1", "split_manifest": "artifacts/splits.json"}],
                        baselines=[{"id": "B", "rationale": "fixture", "tuning_budget": "fixture"}],
                        candidates=[{"id": "C", "rationale": "fixture", "tuning_budget": "fixture"}],
                        ablations=[{"id": "A", "rationale": "fixture", "tuning_budget": "fixture"}],
                        ablation_rationale="fixture", stopping_rule="fixed fixture steps")
        protocol["fairness"].update(axis="compute", rationale="fixture", tuning_policy="fixture", capacity_control="fixture")
        rf.write_json(self.project / "protocol.json", protocol)
        self.quiet(rf.freeze, self.args)
        self.key = rf.current(self.project)[0]

    def quiet(self, function, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return function(*args)

    def put(self, name, content):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_input(self, name, model="B", seed=1, kind="confirmatory", value=1.0, status="completed", seconds=1, gpus=0):
        self.put(f"artifacts/{name}.log", f"Synthetic fixture {name}\n")
        rf.write_json(self.project / f"artifacts/{name}.metrics.json", {"loss": value})
        data = {"id": name, "protocol_sha256": rf.current(self.project)[0], "kind": kind, "status": status,
                "model_id": model, "dataset_id": "D", "seed": seed, "command": "fixture command, not executed",
                "code_revision": "test-fixture", "code_artifact": "artifacts/code.py", "environment_file": "artifacts/environment.txt",
                "log_file": f"artifacts/{name}.log", "metrics_file": f"artifacts/{name}.metrics.json",
                "elapsed_seconds": seconds, "gpu_count": gpus, "failure_reason": "synthetic failure" if status == "failed" else ""}
        path = self.project / f"artifacts/{name}.input.json"
        rf.write_json(path, data)
        return argparse.Namespace(project=self.project, file=path)

    def add_run(self, *args, **kwargs):
        return self.quiet(rf.record, self.run_input(*args, **kwargs))

    def add_review(self, name, scope, issues=None):
        data = {"id": name, "scope": scope, "protocol_sha256": rf.current(self.project)[0],
                "reviewer": "synthetic unit-test fixture, not an actual review", "assessment": "fixture", "issues": issues or []}
        path = self.project / f"artifacts/{name}.input.json"
        rf.write_json(path, data)
        self.quiet(rf.register_review, argparse.Namespace(project=self.project, file=path))

    def pilot(self):
        self.add_run("PILOT", kind="pilot")
        data = rf.read_json(self.project / "pilot.json")
        data["protocol_sha256"] = rf.current(self.project)[0]
        for entry in data["checks"]:
            entry.update(status="pass", reason="Synthetic fixture only", artifacts=["artifacts/pilot.txt"])
        rf.write_json(self.project / "pilot.json", data)
        self.add_review("RV-pilot", "pilot")

    def experiments(self):
        self.pilot()
        # C is deliberately worse than B: the workflow must accept a negative result.
        for model, base in (("B", 1.0), ("C", 5.0), ("A", 2.0)):
            for seed in (1, 2):
                self.add_run(f"{model}{seed}", model=model, seed=seed, value=base + seed)
        self.quiet(rf.summarize, self.args)
        self.put("reports/analysis.md", "Fixture analysis: the candidate loses; report the negative result.\n")
        self.add_review("RV-experiments", "experiments")

    def paper(self):
        self.experiments()
        rf.write_json(self.project / "claims.json", {"claims": [{
            "id": "CL1", "text": "Fixture negative result", "kind": "empirical", "status": "qualified",
            "included_in_paper": True, "scope": "unit-test fixture", "limitation": "not scientific evidence",
            "location": "section 1", "run_ids": ["B1", "B2", "C1", "C2"], "paper_ids": ["P_TEST"],
            "artifacts": ["reports/analysis.md", "reports/summary.json"],
        }]})
        self.put("paper/manuscript.md", "# Unit test\n\nMock citation [@P_TEST]. Negative fixture result.\n")
        self.put("paper/references.bib", "@misc{P_TEST, title={MOCK PAPER FOR UNIT TEST ONLY}}\n")
        self.add_review("RV-paper", "paper")

    def test_initialization_is_portable_and_refuses_overwrite(self):
        self.assertTrue((self.project / ".agents/skills/research-paper/references/records.md").is_file())
        output = subprocess.run([sys.executable, str(self.project / "tools/research.py"), "status", "--project", str(self.project), "--json"], capture_output=True, text=True)
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(json.loads(output.stdout)["stage"], "pilot")
        with self.assertRaises(rf.Problem):
            self.quiet(rf.init_project, argparse.Namespace(project=self.project, topic="overwrite"))

    def test_empty_workspace_fails_scope_and_advance(self):
        empty = Path(self.temporary.name) / "empty"
        self.quiet(rf.init_project, argparse.Namespace(project=empty, topic="topic"))
        outcome = subprocess.run([sys.executable, str(empty / "tools/research.py"), "advance", "--project", str(empty)], capture_output=True, text=True)
        self.assertEqual(outcome.returncode, 2)
        self.assertEqual(rf.metadata(empty)["stage"], "scope")

    def test_freeze_requires_reason_and_preserves_history(self):
        self.add_run("OLD", kind="pilot")
        self.put("artifacts/evaluate.py", "# A revised fixture metric implementation\n")
        with self.assertRaises(rf.Problem):
            rf.current(self.project)
        with self.assertRaises(rf.Problem):
            self.quiet(rf.freeze, self.args)
        self.args.reason = "Correct fixture metric"
        self.quiet(rf.freeze, self.args)
        self.assertNotEqual(self.key, rf.current(self.project)[0])
        self.assertEqual(len(rf.runs(self.project)), 1)
        self.assertEqual(len(rf.summary(self.project)["missing"]), 6)
        self.assertEqual(len(list((self.project / "protocols").glob("*.json"))), 2)

    def test_duplicate_seeds_and_test_selection_are_rejected(self):
        path = self.project / "protocol.json"
        data = rf.read_json(path)
        data["seeds"] = [1, 1]
        rf.write_json(path, data)
        with self.assertRaises(rf.Problem):
            rf.validate_protocol(self.project)
        data["seeds"] = [1, 2]
        data["fairness"]["selection_split"] = "test"
        rf.write_json(path, data)
        with self.assertRaises(rf.Problem):
            rf.validate_protocol(self.project)

    def test_artifact_escape_is_rejected(self):
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        for name in ("../outside.txt", str(outside)):
            with self.assertRaises(rf.Problem):
                rf.artifact(self.project, name)
        (self.project / "artifacts/escape").symlink_to(outside)
        with self.assertRaises(rf.Problem):
            rf.artifact(self.project, "artifacts/escape")

    def test_duplicate_confirmatory_is_rejected_and_failed_retry_allowed(self):
        self.add_run("FAILED", status="failed")
        self.add_run("DONE")
        with self.assertRaises(rf.Problem):
            self.add_run("DUPLICATE")
        self.assertEqual(len(rf.runs(self.project)), 2)
        self.assertEqual(rf.summary(self.project)["run_ids"], ["DONE"])

    def test_smoke_and_pilot_do_not_count_as_confirmatory(self):
        self.add_run("SMOKE", kind="smoke")
        self.add_run("SHORT", kind="pilot")
        summary = rf.summary(self.project)
        self.assertFalse(summary["rows"])
        self.assertEqual(len(summary["missing"]), 6)

    def test_evidence_is_copied_and_tampering_is_detected(self):
        self.add_run("R1", value=-2)
        self.put("artifacts/R1.metrics.json", '{"loss": 999}')
        self.assertEqual(rf.runs(self.project)[0]["metrics"]["loss"], -2)
        evidence = rf.runs(self.project)[0]["evidence"]["metrics"]["path"]
        self.put(evidence, '{"loss": 999}')
        with self.assertRaisesRegex(rf.Problem, "运行证据被改动"):
            rf.runs(self.project)

    def test_record_metadata_tampering_is_detected(self):
        self.add_run("R1")
        path = self.project / "runs/R1/record.json"
        data = rf.read_json(path)
        data["metrics"]["loss"] = 999
        rf.write_json(path, data)
        with self.assertRaisesRegex(rf.Problem, "记录已被改动"):
            rf.runs(self.project)

    def test_invalid_metrics_and_nonfinite_values_are_rejected(self):
        for value in ("true", "NaN", "Infinity", '"1"'):
            args = self.run_input("BAD")
            self.put("artifacts/BAD.metrics.json", '{"loss": ' + value + "}")
            with self.assertRaises((rf.Problem, ValueError)):
                self.quiet(rf.record, args)
        self.assertEqual(len(rf.runs(self.project)), 0)

    def test_budget_overrun_is_logged_including_failed_runs(self):
        result = self.add_run("OOM", status="failed", seconds=3600, gpus=1)
        self.assertEqual(result, 1)
        records = rf.runs(self.project)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["gpu_hours"], 1)
        self.assertTrue(rf.budget_issues(self.project, records))

    def test_budget_counts_old_protocols(self):
        data = rf.metadata(self.project)
        data["budget"].update(max_gpu_hours=0.5, max_gpu_hours_per_run=0.4)
        rf.write_json(self.project / "project.json", data)
        self.args.reason = "Fixture budget"
        self.quiet(rf.freeze, self.args)
        self.assertEqual(self.add_run("OLD", kind="pilot", seconds=1080, gpus=1), 0)
        self.put("artifacts/evaluate.py", "# New fixture protocol\n")
        self.args.reason = "Fixture protocol change"
        self.quiet(rf.freeze, self.args)
        self.assertEqual(self.add_run("NEW", kind="pilot", seconds=1080, gpus=1), 1)
        self.assertAlmostEqual(sum(x["gpu_hours"] for x in rf.runs(self.project)), 0.6)

    def test_omitted_issues_remain_open(self):
        self.pilot()
        issue = {"id": "I1", "severity": "major", "description": "Fixture issue", "evidence": "fixture", "status": "open"}
        self.add_review("RV-open", "pilot", [issue])
        self.add_review("RV-omitted", "pilot", [])
        with self.assertRaisesRegex(rf.Problem, "I1"):
            rf.check_review(self.project, "pilot")
        issue.update(status="resolved", resolution="Fixture fix", resolution_artifacts=["artifacts/pilot.txt"])
        self.add_review("RV-resolved", "pilot", [issue])
        rf.check_review(self.project, "pilot")

    def test_blocker_cannot_be_accepted(self):
        issue = {"id": "I1", "severity": "blocker", "description": "Fixture issue", "evidence": "fixture", "status": "accepted", "resolution": "fixture", "resolution_artifacts": ["artifacts/pilot.txt"]}
        with self.assertRaises(rf.Problem):
            self.add_review("RV-invalid", "pilot", [issue])

    def test_resolution_evidence_is_bound_to_review(self):
        self.pilot()
        self.put("artifacts/fix-proof.txt", "Original repair evidence")
        issue = {"id": "FIX1", "severity": "major", "description": "Fixture issue", "evidence": "fixture",
                 "status": "resolved", "resolution": "Fixture repair", "resolution_artifacts": ["artifacts/fix-proof.txt"]}
        self.add_review("RV-repaired", "pilot", [issue])
        rf.check_review(self.project, "pilot")
        self.put("artifacts/fix-proof.txt", "Changed repair evidence")
        with self.assertRaisesRegex(rf.Problem, "修复证据已变更"):
            rf.check_review(self.project, "pilot")

    def test_issue_cannot_be_closed_by_lowering_severity(self):
        self.pilot()
        issue = {"id": "I1", "severity": "major", "description": "Fixture issue", "evidence": "fixture", "status": "open"}
        self.add_review("RV-important", "pilot", [issue])
        issue["severity"] = "minor"
        with self.assertRaisesRegex(rf.Problem, "严重级别"):
            self.add_review("RV-downgraded", "pilot", [issue])
        self.assertFalse((self.project / "reviews/RV-downgraded").exists())

    def test_metric_write_race_cannot_produce_inconsistent_archive(self):
        args = self.run_input("RACE", value=1)
        original = rf.shutil.copy2

        def copy_with_concurrent_metric_update(source, destination):
            if Path(source).name == "RACE.metrics.json":
                self.put("artifacts/RACE.metrics.json", '{"loss": 2}')
            return original(source, destination)

        with mock.patch.object(rf.shutil, "copy2", side_effect=copy_with_concurrent_metric_update):
            with self.assertRaisesRegex(rf.Problem, "指标在登记过程中改变"):
                self.quiet(rf.record, args)
        self.assertEqual(len(rf.runs(self.project)), 0)
        self.assertFalse(list((self.project / "runs").glob(".pending-*")))

    def test_review_staleness_and_scope(self):
        self.pilot()
        self.add_run("FORMAL")
        rf.check_review(self.project, "pilot")
        self.put("artifacts/pilot.txt", "Changed pilot evidence\n")
        with self.assertRaisesRegex(rf.Problem, "过期"):
            rf.check_review(self.project, "pilot")

    def test_evaluator_cannot_be_waived_or_removed_after_baseline_runs(self):
        self.pilot()
        path = self.project / "pilot.json"
        original = rf.read_json(path)
        for status in ("na", "pending", "fail"):
            data = json.loads(json.dumps(original))
            next(c for c in data["checks"] if c["name"] == "evaluator_sensitivity")["status"] = status
            rf.write_json(path, data)
            with self.assertRaisesRegex(rf.Problem, "evaluator_sensitivity"):
                rf.check_pilot(self.project)
        original["checks"] = [c for c in original["checks"] if c["name"] != "evaluator_sensitivity"]
        rf.write_json(path, original)
        with self.assertRaisesRegex(rf.Problem, "缺少必要检查"):
            rf.check_pilot(self.project)

    def test_changed_evaluator_audit_invalidates_baseline_approval(self):
        self.pilot()
        self.put("artifacts/evaluator-audit.txt", "Fixture only: controlled outputs were distinguished\n")
        path = self.project / "pilot.json"
        data = rf.read_json(path)
        next(c for c in data["checks"] if c["name"] == "evaluator_sensitivity")["artifacts"] = ["artifacts/evaluator-audit.txt"]
        rf.write_json(path, data)
        self.add_review("RV-evaluator", "pilot")
        rf.check_pilot(self.project)
        self.put("artifacts/evaluator-audit.txt", "Fixture correction: a constant metric was found\n")
        with self.assertRaisesRegex(rf.Problem, "过期"):
            rf.check_pilot(self.project)

    def test_full_grid_accepts_negative_result_and_reports_sample_std(self):
        self.experiments()
        self.assertEqual(rf.check(self.project, "experiments"), [])
        rows = {x["model"]: x for x in rf.summary(self.project)["rows"]}
        self.assertGreater(rows["C"]["mean"], rows["B"]["mean"])
        self.assertAlmostEqual(rows["B"]["sample_std"], 2 ** -0.5)
        self.assertEqual(rows["C"]["n"], 2)

    def test_incomplete_grid_and_single_seed_uncertainty(self):
        self.pilot()
        self.add_run("B1")
        self.quiet(rf.summarize, self.args)
        self.assertIsNone(rf.summary(self.project)["rows"][0]["sample_std"])
        self.assertTrue(any("网格不完整" in x for x in rf.check(self.project, "experiments")))

    def test_stale_analysis_requires_new_review(self):
        self.experiments()
        self.put("reports/analysis.md", "Changed interpretation\n")
        self.assertTrue(any("审查已过期" in x for x in rf.check(self.project, "experiments")))

    def test_paper_requires_current_evidence_and_verified_citation_keys(self):
        self.paper()
        self.assertEqual(rf.check(self.project, "paper"), [])
        self.put("paper/manuscript.md", "Unknown citation [@MISSING].\n")
        self.assertTrue(any("正文引用" in x for x in rf.check(self.project, "paper")))

    def test_mechanistic_claim_requires_ablation(self):
        self.paper()
        path = self.project / "claims.json"
        data = rf.read_json(path)
        data["claims"][0]["kind"] = "mechanistic"
        rf.write_json(path, data)
        self.assertTrue(any("消融运行" in x for x in rf.check(self.project, "paper")))

    def test_unsupported_claim_cannot_appear_in_paper(self):
        self.paper()
        path = self.project / "claims.json"
        data = rf.read_json(path)
        data["claims"][0]["status"] = "unsupported"
        rf.write_json(path, data)
        self.assertTrue(any("未获证据支持" in x for x in rf.check(self.project, "paper")))

    def test_submission_checks_package_without_submitting(self):
        self.paper()
        # Only the documented PDF-header invariant is tested; this is not a rendered PDF.
        self.put("paper/submission.pdf", "%PDF-1.7\nUNIT TEST FIXTURE ONLY\n")
        data = rf.read_json(self.project / "submission.json")
        data.update(venue="fixture", year="2026", track="fixture", policy_url="https://example.org/fixture", checked_at="2026-11-05", package_files=["paper/submission.pdf", "reports/analysis.md"])
        for entry in data["checks"].values():
            entry.update(status="pass", reason="Fixture only; no actual submission", artifacts=["artifacts/pilot.txt"])
        rf.write_json(self.project / "submission.json", data)
        self.assertEqual(rf.check(self.project, "submission"), [])
        self.put("paper/submission.pdf", "not a pdf")
        self.assertTrue(any("PDF 文件头" in x for x in rf.check(self.project, "submission")))


if __name__ == "__main__":
    unittest.main()
