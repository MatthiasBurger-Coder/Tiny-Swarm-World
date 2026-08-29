#!/usr/bin/env python3
"""Run the authorized Classic live chain and write only redacted evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = REPOSITORY_ROOT / ".tiny-swarm-world/local/live-installation.env"
EVIDENCE_ROOT = REPOSITORY_ROOT / ".tiny-swarm-world/evidence/live-greenpath"
TEST_COUNT_PATTERN = re.compile(r"Ran (\d+) tests? in ([0-9.]+)s")
SKIP_PATTERN = re.compile(r"skipped=(\d+)")


@dataclass(frozen=True)
class CommandResult:
    operation: str
    started_at: str
    finished_at: str
    duration_seconds: float
    exit_code: int
    summary: dict[str, object]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--evidence-root", type=Path, default=EVIDENCE_ROOT)
    args = parser.parse_args()

    started_at = _utc_now()
    run_id = started_at.replace("-", "").replace(":", "").replace("+00:00", "Z")
    evidence_dir = args.evidence_root / run_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    _private(evidence_dir)

    if not args.approve_live:
        return _write_terminal_result(
            evidence_dir,
            run_id=run_id,
            started_at=started_at,
            status="LIVE_CONSENT_MISSING",
            operations=(),
            reason="--approve-live was not supplied",
        )

    if not args.env_file.is_file():
        return _write_terminal_result(
            evidence_dir,
            run_id=run_id,
            started_at=started_at,
            status="LIVE_PREREQUISITE_MISSING",
            operations=(),
            reason="live environment source is missing",
        )

    environment = os.environ.copy()
    operations: list[CommandResult] = []
    commands = (
        ("diagnostics", ("python3", "tools/install_debugger.py", "--live"), 120),
        (
            "setup",
            (
                "./tsw",
                "--live",
                "--approve-live",
                "--json",
                "--service-profile",
                "service-access",
                "--allow-wsl-windows-filesystem",
                "setup",
                "run",
            ),
            1800,
        ),
        (
            "platform_verify",
            (
                "./tsw",
                "--json",
                "--service-profile",
                "service-access",
                "--allow-wsl-windows-filesystem",
                "platform",
                "verify",
            ),
            300,
        ),
        (
            "classic_e2e",
            (
                "env",
                "TSW_RUN_POST_INSTALL_BROWSER_LIVE=1",
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests/e2e/classic",
                "-t",
                ".",
            ),
            900,
        ),
    )

    status = "LIVE_VERIFIED"
    for operation, command, timeout in commands:
        result = _run_operation(operation, command, timeout, args.env_file, environment)
        operations.append(result)
        if result.exit_code != 0:
            status = "LIVE_PREREQUISITE_MISSING" if operation == "diagnostics" else "LIVE_FAILED_AFTER_MUTATION"
            break

    return _write_terminal_result(
        evidence_dir,
        run_id=run_id,
        started_at=started_at,
        status=status,
        operations=tuple(operations),
        reason=None,
    )


def _run_operation(
    operation: str,
    command: tuple[str, ...],
    timeout: int,
    env_file: Path,
    environment: dict[str, str],
) -> CommandResult:
    started_at = _utc_now()
    started = monotonic()
    shell_command = f"set -a; . {shlex.quote(env_file.as_posix())}; set +a; exec {shlex.join(command)}"
    try:
        completed = subprocess.run(
            ["bash", "-lc", shell_command],
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        exit_code = completed.returncode
        summary = _summarize(operation, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired:
        exit_code = 124
        summary = {"result": "timed_out", "timeout_seconds": timeout}
    finished_at = _utc_now()
    return CommandResult(
        operation=operation,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=round(monotonic() - started, 3),
        exit_code=exit_code,
        summary=summary,
    )


def _summarize(operation: str, stdout: str, stderr: str) -> dict[str, object]:
    if operation == "classic_e2e":
        match = TEST_COUNT_PATTERN.search(stdout + "\n" + stderr)
        skips = SKIP_PATTERN.search(stdout + "\n" + stderr)
        return {
            "result": "passed" if "OK" in stdout + stderr and "FAILED" not in stdout + stderr else "failed",
            "tests": int(match.group(1)) if match else None,
            "runtime_seconds": float(match.group(2)) if match else None,
            "skipped": int(skips.group(1)) if skips else 0,
        }
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return {"result": "completed_without_structured_summary" if not stderr else "failed"}
    if not isinstance(payload, dict):
        return {"result": "completed_without_structured_summary"}
    outcome = payload.get("outcome")
    outcome_dict = outcome if isinstance(outcome, dict) else {}
    verification_results = outcome_dict.get("verification_results")
    result_count = len(verification_results) if isinstance(verification_results, list) else 0
    return {
        "status": payload.get("status"),
        "verification": outcome_dict.get("verification"),
        "mutation": outcome_dict.get("mutation", {}).get("result")
        if isinstance(outcome_dict.get("mutation"), dict)
        else None,
        "result_count": result_count,
    }


def _write_terminal_result(
    evidence_dir: Path,
    *,
    run_id: str,
    started_at: str,
    status: str,
    operations: tuple[CommandResult, ...],
    reason: str | None,
) -> int:
    finished_at = _utc_now()
    payload = {
        "run_id": run_id,
        "repository_commit": _git_commit(),
        "scenario": "classic_live_chain",
        "host_class": _host_class(),
        "consent_state": "LIVE_APPROVED" if status != "LIVE_CONSENT_MISSING" else status,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "status": status,
        "reason": reason,
        "operations": [
            {
                "operation": operation.operation,
                "started_at_utc": operation.started_at,
                "finished_at_utc": operation.finished_at,
                "duration_seconds": operation.duration_seconds,
                "exit_code": operation.exit_code,
                "summary": operation.summary,
            }
            for operation in operations
        ],
        "redaction": "raw stdout, stderr, credentials and environment values were not written",
    }
    summary_path = evidence_dir / "run-summary.json"
    summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _private(summary_path)
    checksum_path = evidence_dir / "checksums.sha256"
    digest = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  run-summary.json\n", encoding="utf-8")
    _private(checksum_path)
    checksum_digest = hashlib.sha256(checksum_path.read_bytes()).hexdigest()
    terminal_path = evidence_dir / "checksums.sha256.sha256"
    terminal_path.write_text(f"{checksum_digest}  checksums.sha256\n", encoding="utf-8")
    _private(terminal_path)
    return 0 if status == "LIVE_VERIFIED" else 1


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _host_class() -> str:
    if Path("/run/WSL").exists() or "microsoft" in platform.release().casefold():
        return "wsl2"
    return "native_linux"


def _private(path: Path) -> None:
    path.chmod(0o700 if path.is_dir() else 0o600)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
