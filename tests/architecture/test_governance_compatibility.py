import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestGovernanceCompatibility(unittest.TestCase):
    def test_public_process_commands_remain_explicitly_routed(self):
        routing = (ROOT / ".agents/orchestrator/routing-rules.md").read_text(encoding="utf-8")
        for command in ("skills update", "workflow create", "workflow execute"):
            self.assertIn(command, routing)
        executor = (ROOT / ".agents/skills/workflow-executor/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("push auto", executor)

    def test_execution_protocol_preserves_required_safety_controls(self):
        executor = (ROOT / ".agents/skills/workflow-executor/SKILL.md").read_text(encoding="utf-8")
        for invariant in (
            "S3/S3D",
            "issue-completion-auditor",
            "Typed Error Router",
            "required quality gate",
            "Slice checkpoint push is not `push auto`",
        ):
            self.assertIn(invariant, executor)

    def test_project_identity_excludes_retired_process_surfaces(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("not a Spring Boot application", agents)
        self.assertIn("not a React frontend project", agents)

    def test_orchestrator_responsibilities_have_one_authority_each(self):
        model = (ROOT / ".agents/orchestrator/responsibility-model.md").read_text(encoding="utf-8")
        for component in (
            "Command Router",
            "Activation Resolver",
            "Planner / S3D",
            "Lock Coordinator",
            "Slice Executor",
            "Completion Auditor",
            "Publication Guard",
        ):
            self.assertIn(component, model)
        self.assertIn("cannot call back into routing", model)


if __name__ == "__main__":
    unittest.main()
