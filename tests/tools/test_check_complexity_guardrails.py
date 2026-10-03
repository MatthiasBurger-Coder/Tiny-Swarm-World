from __future__ import annotations

import copy
from pathlib import Path
import tempfile
from typing import Any
import unittest

from tools import check_complexity_guardrails as guard


class ComplexityGuardrailTests(unittest.TestCase):
    def test_discovery_includes_new_application_owner_and_root_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for name in ("new_entrypoint.py", "application/services/cli_dispatch.py",
                         "infrastructure/adapters/cli/dispatcher.py",
                         "infrastructure/adapters/clients/lxc/provider.py"):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("pass\n", encoding="utf-8")
            found = {path.relative_to(source).as_posix() for path in guard.covered_paths(source)}
            self.assertEqual({"new_entrypoint.py", "application/services/cli_dispatch.py",
                              "infrastructure/adapters/cli/dispatcher.py",
                              "infrastructure/adapters/clients/lxc/provider.py"}, found)

    def _snapshot(self, files: dict[str, str]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for name, source in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")
                paths.append(path)
            return guard.snapshot(paths, root)

    def test_snapshot_records_function_class_module_and_import_metrics(self) -> None:
        state = self._snapshot({"a.py": "import os\nfrom pathlib import Path\nclass A:\n"
                                "    def run(self, ready):\n        if ready and os.name:\n"
                                "            return Path('.')\n        return None\n"})
        module = state["modules"]["a.py"]
        self.assertEqual(2, module["fanout"])
        self.assertEqual(3, module["functions"]["A.run"]["complexity"])
        self.assertGreater(module["classes"]["A"]["lines"], 0)

    def test_new_and_grown_critical_functions_require_review(self) -> None:
        base = self._snapshot({"a.py": "def stable():\n    pass\n"})
        body = "def complex_work():\n" + "    if flag:\n        pass\n" * 15 + "    pass\n" * 35
        current = self._snapshot({"a.py": body})
        self.assertIn("new-critical-function:a.py:complex_work", guard.findings(current, base))
        self.assertEqual([], guard.findings(base, base))
        grown = copy.deepcopy(current)
        grown["modules"]["a.py"]["functions"]["complex_work"]["complexity"] += 4
        self.assertIn("grown-critical-function:a.py:complex_work", guard.findings(grown, current))

    def test_existing_function_crossing_critical_boundary_requires_review(self) -> None:
        base = self._snapshot({"a.py": "def work():\n    pass\n"})
        current = copy.deepcopy(base)
        base_metric = base["modules"]["a.py"]["functions"]["work"]
        base_metric.update({"complexity": 14, "lines": 59})
        current["modules"]["a.py"]["functions"]["work"].update(
            {"complexity": 15, "lines": 60})
        self.assertIn("newly-critical-function:a.py:work", guard.findings(current, base))

    def test_size_alone_does_not_fail_and_coupled_growth_does(self) -> None:
        base = self._snapshot({"a.py": "import os\ndef work():\n    pass\n"})
        larger = copy.deepcopy(base)
        larger["modules"]["a.py"]["lines"] += 500
        self.assertEqual([], guard.findings(larger, base))
        larger["modules"]["a.py"]["complexity"] += 10
        larger["modules"]["a.py"]["fanout"] += 3
        self.assertIn("grown-module-coupling:a.py", guard.findings(larger, base))

    def test_large_single_signal_module_growth_requires_review(self) -> None:
        base = self._snapshot({"a.py": "def stable():\n    pass\n"})
        complex_growth = copy.deepcopy(base)
        complex_growth["modules"]["a.py"]["complexity"] += 25
        self.assertIn("grown-module-complexity:a.py", guard.findings(complex_growth, base))
        fanout_growth = copy.deepcopy(base)
        fanout_growth["modules"]["a.py"]["fanout"] += 8
        self.assertIn("grown-module-fanout:a.py", guard.findings(fanout_growth, base))

    def test_new_duplicate_orchestration_is_detected(self) -> None:
        repeated = "def execute(value):\n" + "    if value:\n        value += 1\n" * 8 + "    return value\n"
        base = self._snapshot({"a.py": repeated})
        current = self._snapshot({"a.py": repeated, "b.py": repeated.replace("execute", "run")})
        self.assertEqual(1, len(current["duplicates"]))
        self.assertTrue(any(item.startswith("new-duplicate-orchestration:")
                            for item in guard.findings(current, base)))

    def test_new_critical_class_and_module_require_review(self) -> None:
        base = self._snapshot({"a.py": "def stable():\n    pass\n"})
        current = copy.deepcopy(base)
        module = current["modules"]["a.py"]
        module["classes"]["Coordinator"] = {"complexity": 25, "lines": 120}
        module["lines"] = 300
        module["complexity"] = 40
        module["fanout"] = 12
        self.assertIn("new-critical-class:a.py:Coordinator", guard.findings(current, base))
        new_module = copy.deepcopy(module)
        current["modules"]["b.py"] = new_module
        self.assertIn("new-critical-module:b.py", guard.findings(current, base))

    def test_existing_module_crossing_critical_boundary_requires_review(self) -> None:
        base = self._snapshot({"a.py": "def stable():\n    pass\n"})
        current = copy.deepcopy(base)
        base["modules"]["a.py"].update({"complexity": 39, "fanout": 11, "lines": 299})
        current["modules"]["a.py"].update({"complexity": 40, "fanout": 12, "lines": 300})
        self.assertIn("newly-critical-module:a.py", guard.findings(current, base))

    def test_disappearing_covered_module_requires_review(self) -> None:
        base = self._snapshot({"a.py": "pass\n"})
        current = self._snapshot({"b.py": "pass\n"})
        self.assertIn("missing-covered-module:a.py", guard.findings(current, base))

    def test_existing_class_crossing_critical_boundary_requires_review(self) -> None:
        base = self._snapshot({"a.py": "class Coordinator:\n    pass\n"})
        current = copy.deepcopy(base)
        base["modules"]["a.py"]["classes"]["Coordinator"].update(
            {"complexity": 24, "lines": 119})
        current["modules"]["a.py"]["classes"]["Coordinator"].update(
            {"complexity": 25, "lines": 120})
        self.assertIn("newly-critical-class:a.py:Coordinator", guard.findings(current, base))

    def test_reviewed_exceptions_require_metadata_and_cannot_be_stale(self) -> None:
        base = self._snapshot({"a.py": "def stable():\n    pass\n"})
        current = copy.deepcopy(base)
        current["modules"]["a.py"]["complexity"] += 10
        current["modules"]["a.py"]["fanout"] += 3
        finding = "grown-module-coupling:a.py"
        self.assertEqual([finding], guard.check(current, base, {"schema": 1, "findings": {}}))
        exception = {finding: {"owner": "architecture", "reason": "tracked", "issue": "#1"}}
        self.assertEqual([], guard.check(current, base, {"schema": 1, "findings": exception}))
        with self.assertRaisesRegex(ValueError, "Stale"):
            guard.check(base, base, {"schema": 1, "findings": exception})
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            guard.check(current, base, {"schema": 1, "findings": {finding: {"reason": "tracked"}}})


if __name__ == "__main__":
    unittest.main()
