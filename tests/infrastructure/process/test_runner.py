import subprocess
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.process import (
    ProcessExecutionError,
    ProcessLaunchError,
    ProcessTimeoutError,
    SubprocessProcessRunner,
)


class TestSubprocessProcessRunner(unittest.TestCase):
    @patch("tiny_swarm_world.infrastructure.process.runner.subprocess.run")
    def test_run_text_uses_argv_shell_false_and_forwards_options(self, run):
        run.return_value = subprocess.CompletedProcess(
            ["tool", "inspect"],
            0,
            stdout="result",
            stderr="",
        )
        runner = SubprocessProcessRunner()

        result = runner.run_text(
            ["tool", "inspect"],
            cwd="/tmp/workspace",
            env={"SAFE": "value"},
            input="payload",
            timeout=7,
        )

        self.assertEqual(result.stdout, "result")
        self.assertEqual(run.call_args.args[0], ("tool", "inspect"))
        self.assertEqual(run.call_args.kwargs["cwd"], "/tmp/workspace")
        self.assertEqual(run.call_args.kwargs["env"], {"SAFE": "value"})
        self.assertEqual(run.call_args.kwargs["input"], "payload")
        self.assertEqual(run.call_args.kwargs["timeout"], 7)
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertFalse(run.call_args.kwargs["check"])

    @patch("tiny_swarm_world.infrastructure.process.runner.subprocess.run")
    def test_run_bytes_preserves_bytes(self, run):
        run.return_value = subprocess.CompletedProcess(
            ["tool", "load"],
            0,
            stdout=b"result",
            stderr=b"",
        )

        result = SubprocessProcessRunner().run_bytes(
            ["tool", "load"],
            input=b"payload",
            timeout=3,
        )

        self.assertEqual(result.stdout, b"result")
        self.assertEqual(run.call_args.kwargs["input"], b"payload")
        self.assertFalse(run.call_args.kwargs["text"])
        self.assertEqual(run.call_args.kwargs["timeout"], 3)

    @patch(
        "tiny_swarm_world.infrastructure.process.runner.subprocess.run",
        side_effect=FileNotFoundError("secret-executable"),
    )
    def test_launch_failure_is_sanitized(self, _run):
        with self.assertRaises(ProcessLaunchError) as raised:
            SubprocessProcessRunner().run_text(["secret-executable"])

        self.assertEqual(str(raised.exception), "Process executable could not be launched.")
        self.assertNotIn("secret-executable", str(raised.exception))

    @patch(
        "tiny_swarm_world.infrastructure.process.runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["secret-command"], 1),
    )
    def test_timeout_is_sanitized(self, _run):
        with self.assertRaises(ProcessTimeoutError) as raised:
            SubprocessProcessRunner().run_text(["secret-command"], timeout=1)

        self.assertEqual(str(raised.exception), "Process execution timed out.")
        self.assertNotIn("secret-command", str(raised.exception))

    @patch("tiny_swarm_world.infrastructure.process.runner.subprocess.run")
    def test_check_maps_nonzero_result_without_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            ["tool"],
            17,
            stdout="secret-output",
            stderr="secret-error",
        )

        with self.assertRaises(ProcessExecutionError) as raised:
            SubprocessProcessRunner().run_text(["tool"], check=True)

        self.assertEqual(raised.exception.returncode, 17)
        self.assertEqual(str(raised.exception), "Process execution failed with exit code 17.")
        self.assertNotIn("secret-output", str(raised.exception))
        self.assertNotIn("secret-error", str(raised.exception))

    def test_default_timeout_is_positive_and_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            SubprocessProcessRunner(0)
        with self.assertRaises(ValueError):
            SubprocessProcessRunner(float("inf"))


if __name__ == "__main__":
    unittest.main()
