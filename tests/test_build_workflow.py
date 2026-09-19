from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "source" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import build_workflow  # noqa: E402


class BuildWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assets = build_workflow.load_assets()
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def args(self, workflow_type: str, iteration: int, plan: dict | None = None):
        plan_path = self.root / f"{workflow_type}-{iteration}.json"
        if plan is not None:
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        return argparse.Namespace(
            workflow_type=workflow_type,
            task_id="task-1",
            iteration=iteration,
            plan_file=str(plan_path),
            decision_file="",
            task_work_dir=str(self.root),
            store_root=str(self.root),
            deadline_minutes=20,
            interaction_mode=None,
        )

    def test_current_preflight_search_and_probe_compile(self) -> None:
        preflight = build_workflow.build_preflight(self.args("preflight", 0), self.assets)
        self.assertTrue(any(step["id"] == "open-channel-search" for step in preflight["steps"]))

        search = build_workflow.build_search(
            self.args(
                "search",
                1,
                {
                    "primary_query": "AI Agent LangGraph",
                    "site_filters": {},
                    "hard_filters": {},
                    "semantic_criteria": {
                        "must_have": ["Agent 经验"],
                        "nice_to_have": [],
                        "exclude_signals": [],
                    },
                },
            ),
            self.assets,
        )
        self.assertTrue(any("pacing" in json.dumps(step) for step in search["steps"]))

        probe = build_workflow.build_probe(
            self.args(
                "probe",
                1,
                {"anchor": "AI Agent", "companies": ["阿里巴巴"], "site_filters": {}},
            ),
            self.assets,
        )
        self.assertEqual(probe["input_summary"]["probe"], True)
        self.assertEqual(probe["steps"][-1]["value"]["summary"]["workflow"], "company_probe")

    def test_channel_default_compiles_human_interaction_metadata(self) -> None:
        workflow = build_workflow.build_preflight(self.args("preflight", 0), self.assets)
        self.assertEqual(workflow["interaction_mode"], "human")
        self.assertIn("interaction.human.v1", workflow["required_capabilities"])

    def test_direct_override_omits_human_capability(self) -> None:
        args = self.args("preflight", 0)
        args.interaction_mode = "direct"
        workflow = build_workflow.build_preflight(args, self.assets)
        self.assertEqual(workflow["interaction_mode"], "direct")
        self.assertNotIn("interaction.human.v1", workflow["required_capabilities"])

    def test_human_search_browses_details_without_removing_pacing(self) -> None:
        workflow = build_workflow.build_search(
            self.args(
                "search",
                1,
                {
                    "primary_query": "AI Agent LangGraph",
                    "site_filters": {},
                    "hard_filters": {},
                    "semantic_criteria": {
                        "must_have": ["Agent 经验"],
                        "nice_to_have": [],
                        "exclude_signals": [],
                    },
                },
            ),
            self.assets,
        )
        encoded = json.dumps(workflow, ensure_ascii=False)
        self.assertIn('"op": "page.scroll"', encoded)
        self.assertIn("pacing-before", encoded)

    def test_human_probe_keeps_company_probe_behavior(self) -> None:
        workflow = build_workflow.build_probe(
            self.args(
                "probe",
                1,
                {"anchor": "AI Agent", "companies": ["阿里巴巴"], "site_filters": {}},
            ),
            self.assets,
        )
        self.assertEqual(workflow["interaction_mode"], "human")
        self.assertEqual(workflow["steps"][-1]["value"]["summary"]["workflow"], "company_probe")

    def test_search_plan_accepts_requirement_version_and_decision_basis(self) -> None:
        path = self.root / "plan.json"
        basis = {
            "requirement_version": "v1",
            "completed_iteration": 0,
            "candidate_scores": [],
            "prf_decision": {"status": "none", "reason": "首轮尚无候选人"},
            "next_action": {
                "action": "search",
                "iteration": 1,
                "primary_query": "AI Agent",
                "reason": "开始首轮",
            },
        }
        path.write_text(
            json.dumps(
                {
                    "requirement_version": "v1",
                    "primary_query": "AI Agent",
                    "site_filters": {},
                    "hard_filters": {},
                    "semantic_criteria": {
                        "must_have": ["Agent 经验"],
                        "nice_to_have": [],
                        "exclude_signals": [],
                    },
                    "decision_basis": basis,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        plan, _ = build_workflow.read_plan(str(path))
        self.assertEqual(plan["requirement_version"], "v1")
        self.assertEqual(plan["decision_basis"], basis)
        args = self.args("search", 1, json.loads(path.read_text(encoding="utf-8")))
        workflow = build_workflow.build_search(args, self.assets)
        self.assertEqual(workflow["input_summary"]["requirement_version"], "v1")
        self.assertEqual(args.decision_receipt["completed_iteration"], 0)


if __name__ == "__main__":
    unittest.main()
