"""Check real mypy resolution and failures against the declared wheel layout."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from modules.tsw_core.tools.linux import quality_gate as gate


class TypecheckPackageTests(unittest.TestCase):
    def test_package_mapping_checks_source_and_consumers_without_stale_cache(self):
        run = subprocess.run
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "owned" / "core"
            source.mkdir(parents=True)
            (source / "__init__.py").write_text("")
            (root / "pyproject.toml").write_text(
                '[tool.setuptools.package-dir]\ntiny_swarm_world = "owned/core"\n'
            )
            tests = root / "tests"
            tests.mkdir()
            (tests / "__init__.py").write_text("")

            def build_or_run(command, **kwargs):
                if command[1:4] == ["-m", "pip", "wheel"]:
                    self.assertIn("--no-index", command)
                    destination = Path(command[command.index("--wheel-dir") + 1])
                    with zipfile.ZipFile(destination / "fixture.whl", "w") as wheel:
                        for path in source.glob("*.py"):
                            wheel.write(path, "tiny_swarm_world/" + path.name)
                    return subprocess.CompletedProcess(command, 0, "", "")
                self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
                return run(command, **kwargs)

            cases = (
                ('return 1', 'int', None),
                ('return "wrong"', 'int', 'return-value'),
                ('return 1', 'str', 'assignment'),
            )
            for body, consumer_type, diagnostic in cases:
                with self.subTest(body=body, consumer_type=consumer_type):
                    (source / "value.py").write_text(f"def value() -> int:\n    {body}\n")
                    (tests / "consumer.py").write_text(
                        "from tiny_swarm_world.value import value\n"
                        f"result: {consumer_type} = value()\n"
                    )
                    output = StringIO()
                    with patch.object(gate, "REPOSITORY_ROOT", root), \
                            patch.object(gate, "SOURCE_ROOT", source), \
                            patch.object(gate, "TEST_ROOTS", [tests]), \
                            patch.object(gate.subprocess, "run", side_effect=build_or_run), \
                            redirect_stdout(output):
                        if diagnostic:
                            with self.assertRaises(SystemExit) as stopped:
                                gate._run_typecheck()
                            self.assertNotEqual(stopped.exception.code, 0)
                        else:
                            gate._run_typecheck()
                    text = output.getvalue()
                    self.assertNotIn("import-not-found", text)
                    if diagnostic:
                        self.assertIn(f"[{diagnostic}]", text)
                    if diagnostic == "return-value":
                        self.assertIn(str(source / "value.py"), text)
