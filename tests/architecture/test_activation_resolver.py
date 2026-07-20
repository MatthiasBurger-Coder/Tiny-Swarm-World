import importlib.util
import unittest
from pathlib import Path


_RESOLVER_PATH = (
    Path(__file__).resolve().parents[2] / ".agents" / "activation" / "resolver.py"
)
_SPEC = importlib.util.spec_from_file_location("skill_activation_resolver", _RESOLVER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
ActivationContext = _MODULE.ActivationContext
resolve_activation = _MODULE.resolve_activation


class TestActivationResolver(unittest.TestCase):
    def test_resolver_requires_evidence_for_conditional_skill(self):
        decision = resolve_activation(
            ActivationContext("workflow execute"),
            frozenset({"frontend-react"}),
        )
        self.assertEqual(decision.selected_skills, ())
        self.assertEqual((decision.activated_count, decision.rejected_count), (0, 1))

    def test_resolver_requires_explicit_approval_for_external_skill(self):
        decision = resolve_activation(
            ActivationContext("workflow execute"),
            frozenset({"external:vendor-skill"}),
        )
        self.assertEqual(decision.selected_skills, ())
        self.assertEqual((decision.activated_count, decision.rejected_count), (0, 1))

    def test_resolver_selects_approved_context_without_changing_command(self):
        decision = resolve_activation(
            ActivationContext(
                "workflow execute",
                frozenset({"verified-frontend-module"}),
                frozenset({"external:vendor-skill"}),
            ),
            frozenset({"frontend-react", "external:vendor-skill"}),
        )
        self.assertEqual(decision.selected_skills, ("external:vendor-skill", "frontend-react"))
        self.assertEqual(decision.command, "workflow execute")
        self.assertTrue(decision.gates_immutable)
        self.assertEqual((decision.activated_count, decision.rejected_count), (2, 0))


if __name__ == "__main__":
    unittest.main()
