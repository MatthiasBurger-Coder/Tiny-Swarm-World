import unittest

from tools.skill_audit import audit, audit_activation, classify_skill


class TestSkillAudit(unittest.TestCase):
    def test_current_registry_has_no_blocking_discovery_findings(self):
        result = audit()
        self.assertEqual(result["result"], "passed")
        self.assertEqual(result["project_skill_entrypoints"], 132)
        self.assertEqual(result["findings"], [])
        self.assertEqual(len(result["classifications"]), 132)
        self.assertEqual(set(result["classifications"].values()) - {
            "governance", "security", "runtime", "quality", "ui", "contracts", "orchestration", "architecture"
        }, set())

    def test_every_skill_has_a_stable_classification(self):
        self.assertEqual(classify_skill("acceptance-checks"), "quality")
        self.assertEqual(classify_skill("workflow-executor"), "orchestration")

    def test_unnecessary_activation_is_blocking(self):
        result = audit_activation({"governance", "unused"}, {"governance"})
        self.assertEqual(result["result"], "failed")
        self.assertEqual(result["activated_count"], 2)
        self.assertEqual(result["findings"][0]["code"], "UNNECESSARY_SKILL_ACTIVATION")


if __name__ == "__main__":
    unittest.main()
