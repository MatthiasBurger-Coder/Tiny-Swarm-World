"""Native guided handoff. Child commands own inventory, consent and mutations."""

from __future__ import annotations

import os
import re
import shlex
import signal
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, NoReturn

from tiny_swarm_world.infrastructure.adapters.guided_setup_state import GuidedSetupState
from tiny_swarm_world.infrastructure.process.streaming import ForegroundTerminationRequested, run_foreground_process
from tiny_swarm_world.infrastructure.process.runner import run_process

PREPARE = "./modules/tsw_native_linux/boostrap/prepare_linux.sh"
INSTALL = "./install.sh"
PLAN_PREFIX = "Guided plan fingerprint: "
GUIDED_COMMITTED_PREFIX = "Guided committed installation: "
GUIDED_PLAN_REFUSED = 65
PLAN_ENV = "TSW_GUIDED_PLAN_NONCE"
EXPECTED_ENV = "TSW_GUIDED_PLAN_EXPECTED"


class SetupExit(Exception):
    def __init__(self, code: int) -> None:
        self.code = code


class GuidedSetup:
    def __init__(self, profile: str, verbose: bool) -> None:
        self.profile_args = ("--service-profile", profile)
        self.command = shlex.join(("./setup_linux.sh", "--profile", profile))
        if verbose:
            self.command += " --verbose"
        self.verbose = verbose
        self.profile = profile
        self.stage = "preflight"
        state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
        self.state = GuidedSetupState(state_home, profile)
        self.lease: tuple[int, ...] = ()

    def stop(self, outcome: str, message: str, code: int, *, next_mode: str = "--dry-run") -> NoReturn:
        next_command = f"{self.command} {next_mode}".rstrip()
        print(f"{outcome} at {self.stage}: {message} Next: {next_command}", file=sys.stderr)
        raise SetupExit(code)

    def run(
        self, stage: str, *args: str, capture: bool = False, read_only: bool = False,
        env: Mapping[str, str] | None = None,
    ) -> tuple[int, str]:
        self.stage = stage
        if self.verbose:
            print(f"Setup stage: {stage}", file=sys.stderr)
        return run_foreground_process(
            args, capture=capture, timeout_seconds=240 if read_only else None,
            lease=self.lease, env=env,
        )

    def report_prior(self, prior: dict[str, Any]) -> None:
        print(f"PARTIAL: Previous {prior['stage']} stage recorded {prior['status']}. "
              "Rechecking current state. Preserve protected preparation backups and installation logs.",
              file=sys.stderr)

    def child_exit(self, code: int, *, mutating: bool) -> NoReturn:
        stage = self.stage
        outcome, result = {124: ("TIMEOUT", 124), 130: ("INTERRUPTED", 130), 143: ("INTERRUPTED", 130)}.get(
            code, ("PARTIAL", 1) if mutating else ("BLOCKED", 2)
        )
        if code == GUIDED_PLAN_REFUSED and stage in {"plan", "install"} and not mutating:
            self.stop("BLOCKED", "Review the installer admission message and preserve the checkpoint.", 2)
        if code == 3 and stage in {"prepare", "preflight"}:
            outcome, result = "RESTART_REQUIRED", 3
        detail = f"(child exit {code})."
        if mutating:
            status = "partial"
            if outcome == "RESTART_REQUIRED":
                status = "restart_required"
            elif outcome == "INTERRUPTED":
                status = "interrupted"
            try:
                self.state.checkpoint(stage, status, code if 0 <= code <= 255 else None)
            except OSError:
                print("Protected checkpoint update failed. The saved intent still requires review.", file=sys.stderr)
            detail += " Partial or uncertain effects are possible. Preserve protected evidence and backups."
        next_mode = "--resume" if mutating else "--dry-run"
        if outcome == "RESTART_REQUIRED" and not mutating:
            retained = self.state.prior() is not None or self.state.has_preparation_record()
            next_mode = "--resume" if retained else ""
        self.stop(outcome, detail, result, next_mode=next_mode)


def read_only(setup: GuidedSetup, mode: str, prior: dict[str, Any] | None) -> int:
    if prior and prior["status"] != "succeeded":
        setup.report_prior(prior)
    code, _ = setup.run("preflight", PREPARE, mode, *setup.profile_args, read_only=True)
    if code:
        setup.child_exit(code, mutating=False)
    code, _ = setup.run("plan", INSTALL, mode, *setup.profile_args, read_only=True)
    if code:
        setup.child_exit(code, mutating=False)
    outcome = "PLAN_READY" if mode == "--dry-run" else "READY"
    print(f"{outcome}: Host preparation and installer checks passed. Service access is unverified.")
    return 0


def prepare(setup: GuidedSetup, prior: dict[str, Any] | None) -> None:
    code, _ = setup.run("preflight", PREPARE, "--dry-run", *setup.profile_args, read_only=True)
    if code == 0:
        print("Host preparation is ready. No preparation changes needed.")
        return
    if code != 2 or (prior and prior["stage"] == "install" and prior["status"] != "succeeded"):
        setup.child_exit(code, mutating=False)
    audit_packages(setup)
    if not setup.state.unchanged_target():
        setup.stop("BLOCKED", "Checkout or target changed during inventory.", 2)
    setup.state.checkpoint("prepare", "started")
    print("Preparation will request consent for each change. Run sudo -v in this terminal if needed.")
    code, _ = setup.run("prepare", PREPARE, *setup.profile_args)
    if code:
        setup.child_exit(code, mutating=True)
    setup.state.checkpoint("prepare", "succeeded", 0)


def preview(setup: GuidedSetup, nonce: str, recovery_args: tuple[str, ...]) -> str | None:
    code, output = setup.run(
        "plan", INSTALL, "--dry-run", *setup.profile_args, "--guided-plan", *recovery_args,
        capture=True, read_only=True, env={**os.environ, PLAN_ENV: nonce, EXPECTED_ENV: ""},
    )
    lines = output.splitlines()
    for line in lines:
        if not line.startswith((PLAN_PREFIX, GUIDED_COMMITTED_PREFIX)):
            print(line)
    if code:
        setup.child_exit(code, mutating=False)
    stamps = [line.removeprefix(PLAN_PREFIX) for line in lines if line.startswith(PLAN_PREFIX)]
    committed = [line.removeprefix(GUIDED_COMMITTED_PREFIX) for line in lines if line.startswith(GUIDED_COMMITTED_PREFIX)]
    if committed:
        if recovery_args and not stamps and len(committed) == 1 and re.fullmatch(r"[0-9a-f]{64}", committed[0]):
            return None
        setup.stop("BLOCKED", "Invalid committed installation observation.", 2)
    if len(stamps) != 1 or not re.fullmatch(r"[0-9a-f]{64}", stamps[0]):
        setup.stop("BLOCKED", "Installation observation is unavailable.", 2)
    return stamps[0]


def apply(setup: GuidedSetup, resume: bool) -> int:
    # Validate existing records before any writes, then re-read under the lease.
    prior = setup.state.prior()
    if resume and prior is None and not setup.state.has_preparation_record():
        setup.stop("BLOCKED", "No setup recovery record found.", 2)
    setup.lease = (setup.state.acquire(),)
    prior = setup.state.prior()
    if prior and (prior["status"] != "succeeded" or prior["stage"] == "prepare"):
        setup.report_prior(prior)
        if not resume and prior["status"] != "succeeded":
            setup.stop("BLOCKED", "Explicit recovery is required.", 2, next_mode="--resume")
    if resume:
        audit_packages(setup)
    prepare(setup, prior)
    nonce = os.urandom(32).hex()
    interrupted_install = prior and prior["stage"] == "install" and prior["status"] != "succeeded"
    recovery_args = ("--guided-resume",) if resume and interrupted_install else ()
    plan = preview(setup, nonce, recovery_args)
    if plan is None:
        if not setup.state.unchanged_target() or setup.state.prior() != prior:
            setup.stop("BLOCKED", "Checkout or recovery checkpoint changed during inventory.", 2)
        setup.state.checkpoint("install", "succeeded", 0)
        print("INSTALLATION_COMPLETE: Recorded the verified installer completion.")
        return 0
    setup.stage = "consent.install"
    print(f"Type yes to proceed to installation for profile {setup.profile}: ",
          end="", flush=True, file=sys.stderr)
    if sys.stdin.readline().removesuffix("\n") != "yes":
        setup.stop("BLOCKED", "Installation consent missing.", 2)
    code, _ = setup.run("preflight", PREPARE, "--dry-run", *setup.profile_args, read_only=True)
    if code:
        setup.child_exit(code, mutating=False)
    if not setup.state.unchanged_target():
        setup.stop("BLOCKED", "Checkout or target changed after consent.", 2)
    setup.stage = "install"
    setup.state.checkpoint("install", "started")
    print(f"Protected guided recovery record: {str(setup.state.root / 'setup.state.json')!r}", flush=True)
    code, _ = setup.run(
        "install", INSTALL, *setup.profile_args, "--guided-report",
        "--guided-plan", *recovery_args,
        env={**os.environ, PLAN_ENV: nonce, EXPECTED_ENV: plan},
    )
    if code == GUIDED_PLAN_REFUSED:
        if prior is None:
            setup.state.checkpoint("prepare", "succeeded", 0)
        else:
            setup.state.restore(prior)
        setup.child_exit(code, mutating=False)
    if code:
        setup.child_exit(code, mutating=True)
    setup.state.checkpoint("install", "succeeded", 0)
    print("Host preparation: complete.\nINSTALLATION_COMPLETE: The installer finished successfully.\n"
          "Service access: unverified from guided setup. See the installation evidence.")
    return 0


def audit_packages(setup: GuidedSetup) -> None:
    result = run_process(
        ("dpkg", "--audit"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
    )
    if result.returncode or result.stdout.strip() or result.stderr.strip():
        setup.stop("BLOCKED", "Package state requires operator review with dpkg --audit.", 2)


def _interrupt(_signum: int, _frame: object) -> None:
    raise ForegroundTerminationRequested


def main(mode: str, profile: str, verbose: bool) -> int:
    if mode not in {"apply", "--resume", "--preflight", "--dry-run"} or profile not in {"default", "service-access"}:
        print("BLOCKED: Use ./setup_linux.sh --help.", file=sys.stderr)
        return 2
    if os.geteuid() == 0 or (mode in {"apply", "--resume"} and not (sys.stdin.isatty() and sys.stdout.isatty())):
        print("BLOCKED: Use ./setup_linux.sh as an ordinary user in an interactive terminal for apply.", file=sys.stderr)
        return 2
    signal.signal(signal.SIGTERM, _interrupt)
    setup: GuidedSetup | None = None
    try:
        setup = GuidedSetup(profile, verbose)
        if mode in {"--preflight", "--dry-run"}:
            return read_only(setup, mode, setup.state.prior())
        return apply(setup, resume=mode == "--resume")
    except SetupExit as error:
        return error.code
    except KeyboardInterrupt:
        print("INTERRUPTED: Preserve the protected checkpoint. Review the same setup command with --dry-run.", file=sys.stderr)
        return 130
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        stage = setup.stage if setup else "preflight"
        partial = stage in {"prepare", "install"}
        outcome = "PARTIAL" if partial else "BLOCKED"
        print(f"{outcome} at {stage}: Checkout, inventory or protected recovery state is unavailable, stale, unsafe or busy. "
              f"Preserve recovery evidence. Next: ./setup_linux.sh --profile {profile} --dry-run", file=sys.stderr)
        return 1 if partial else 2
    finally:
        if setup is not None:
            setup.state.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3] == "true"))
