from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BOOTSTRAP = Path("modules/tsw_native_linux/boostrap")


class SetupLinuxTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory(prefix="tsw setup fixture ")
        self.addCleanup(directory.cleanup)
        self.checkout = Path(directory.name).resolve()
        self.calls = self.checkout / "calls"
        (self.checkout / BOOTSTRAP).mkdir(parents=True)
        (self.checkout / "bin").mkdir()
        for path in (Path("setup_linux.sh"), BOOTSTRAP / "setup_linux.sh"):
            copied = shutil.copy2(ROOT / path, self.checkout / path)
            Path(copied).chmod(0o755)
        self.env = {
            "PATH": f"{self.checkout / 'bin'}:{os.defpath}",
            "CALLS": str(self.calls),
        }
        self._stub("bin/uname", """
case "$1" in
  -s) printf '%s\\n' "${MOCK_SYSTEM:-Linux}" ;;
  -m) printf '%s\\n' "${MOCK_ARCH:-x86_64}" ;;
  -r) printf '%s\\n' "${MOCK_KERNEL:-linux}" ;;
  *) exit 1 ;;
esac
""")
        self._stub("bin/git", """
case "$*" in
  'rev-parse --show-toplevel') printf '%s\\n' "$PWD" ;;
  'rev-parse --verify HEAD')
    if [[ "${MOCK_DRIFT:-0}" == 1 && -e "$CALLS" ]]; then
      printf 'changed-revision\\n'
    else
      printf 'initial-revision\\n'
    fi ;;
  *) exit 1 ;;
esac
""")
        self._stub(BOOTSTRAP / "prepare_linux.sh", """
[[ "$TSW_REPOSITORY_ROOT" == "$PWD" && "$TSW_INFRA_ROOT" == "$PWD/modules/tsw_core/infra" ]] || exit 99
printf 'prepare %s\\n' "$*" >> "$CALLS"
if [[ "${MOCK_PREPARE_CONSENT:-0}" == 1 ]]; then
  IFS= read -r answer && [[ "$answer" == yes ]] || exit 2
fi
exit "${MOCK_PREPARE_EXIT:-0}"
""")
        self._stub("install.sh", """
[[ "$TSW_REPOSITORY_ROOT" == "$PWD" && "$TSW_INFRA_ROOT" == "$PWD/modules/tsw_core/infra" ]] || exit 99
printf 'install %s\\n' "$*" >> "$CALLS"
case "$1" in
  --preflight|--dry-run) exit "${MOCK_PLAN_EXIT:-0}" ;;
  *) exit "${MOCK_INSTALL_EXIT:-0}" ;;
esac
""")

    def _stub(self, relative: str | Path, body: str) -> None:
        path = self.checkout / relative
        path.write_text("#!/usr/bin/env bash\nset -eu\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def _command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.checkout / "setup_linux.sh"), *args], cwd="/",
            env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=10,
        )

    def _guided(self, answers: bytes) -> subprocess.CompletedProcess[bytes]:
        master, terminal = os.openpty()
        try:
            os.write(master, answers)
            return subprocess.run(
                [str(self.checkout / "setup_linux.sh")], cwd="/", env=self.env,
                stdin=terminal, stdout=terminal, stderr=subprocess.PIPE, timeout=10,
            )
        finally:
            os.close(terminal)
            os.close(master)

    def _observed(self) -> list[str]:
        return self.calls.read_text(encoding="utf-8").splitlines() if self.calls.exists() else []

    def _require_ordinary_user(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("The setup entrypoint requires an ordinary user.")

    def test_help_and_invalid_arguments_do_not_inspect_host(self) -> None:
        for name in ("git", "uname", "python3"):
            self._stub(f"bin/{name}", 'printf "unexpected probe\\n" >> "$CALLS"\nexit 1\n')
        help_result = self._command("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--dry-run", help_result.stdout)
        for arguments in (
            ("--help", "--confirm-reset"), ("--preflight", "--dry-run"),
            ("--profile",), ("--profile", "classic"), ("--profile", "minimal"),
            ("--non-interactive-live-approval",), ("--install-dir", "/other"),
        ):
            with self.subTest(arguments=arguments):
                self.assertEqual(self._command(*arguments).returncode, 2)
        self.assertEqual(self._observed(), [])

    def test_unsupported_host_stops_before_either_child(self) -> None:
        for name, value in (
            ("MOCK_SYSTEM", "Darwin"), ("MOCK_ARCH", "aarch64"),
            ("MOCK_KERNEL", "microsoft-standard-WSL2"), ("WSL_INTEROP", "present"),
        ):
            with self.subTest(name=name):
                self.env[name] = value
                result = self._command("--dry-run")
                self.assertEqual(result.returncode, 2)
                self.assertIn("Native Ubuntu", result.stderr)
                del self.env[name]
        self.assertEqual(self._observed(), [])

    def test_read_only_modes_forward_only_read_only_arguments(self) -> None:
        self._require_ordinary_user()
        for mode, outcome in (("--preflight", "READY"), ("--dry-run", "PLAN_READY")):
            with self.subTest(mode=mode):
                result = self._command(mode, "--profile", "default")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(outcome, result.stdout)
                self.assertEqual(self._observed(), [
                    f"prepare {mode} --service-profile default",
                    f"install {mode} --service-profile default",
                ])
                self.calls.unlink()

    def test_apply_requires_terminal_and_one_checkout(self) -> None:
        self._require_ordinary_user()
        result = self._command()
        self.assertEqual(result.returncode, 2)
        self.assertIn("interactive terminal", result.stderr)
        self.env["TSW_INFRA_ROOT"] = "/other-checkout/infra"
        result = self._command("--preflight")
        self.assertEqual(result.returncode, 2)
        self.assertIn("infrastructure paths", result.stderr)
        self.assertEqual(self._observed(), [])

    def test_separate_install_consent_and_same_preset_on_repeat(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_PREPARE_CONSENT"] = "1"
        preview = ["prepare --service-profile service-access",
                   "install --dry-run --service-profile service-access"]
        install = ["install --service-profile service-access"]
        declined = self._guided(b"yes\nno\n")
        self.assertEqual(declined.returncode, 2, declined.stderr)
        self.assertEqual(self._observed(), preview)
        self.calls.unlink()

        for _ in range(2):
            result = self._guided(b"yes\nyes\n")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._observed(), (preview + install) * 2)

    def test_prepare_failures_never_reach_installer(self) -> None:
        self._require_ordinary_user()
        for child, expected in ((1, 1), (2, 2), (3, 3), (4, 1), (124, 124), (130, 130)):
            with self.subTest(child=child):
                self.env["MOCK_PREPARE_EXIT"] = str(child)
                result = self._guided(b"yes\n")
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertIn(f"prepare (child exit {child})".encode(), result.stderr)
                if child == 3:
                    next_command = result.stderr.decode().partition("Next: ")[2]
                    self.assertEqual(shlex.split(next_command), [
                        str(self.checkout / "setup_linux.sh"), "--profile", "service-access",
                    ])
                self.assertEqual(self._observed(), ["prepare --service-profile service-access"])
                self.calls.unlink()

    def test_preview_failure_and_changed_revision_stop_apply(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_PLAN_EXIT"] = "17"
        result = self._guided(b"yes\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"plan (child exit 17)", result.stderr)
        self.assertNotIn(b"Type yes", result.stderr)
        self.assertEqual(len(self._observed()), 2)
        self.calls.unlink()
        self.env["MOCK_PLAN_EXIT"] = "0"
        self.env["MOCK_DRIFT"] = "1"
        result = self._guided(b"yes\n")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"Checkout revision changed", result.stderr)
        self.assertEqual(len(self._observed()), 2)

    def test_installer_failure_keeps_child_exit(self) -> None:
        self._require_ordinary_user()
        self.env["MOCK_INSTALL_EXIT"] = "17"
        result = self._guided(b"yes\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"install (child exit 17)", result.stderr)
        self.assertEqual(self._observed()[-1], "install --service-profile service-access")
