from __future__ import annotations

from pathlib import Path

from tiny_swarm_world.application.ports.host import (
    PortHostPreparation,
    PortWindowsCommandRunner,
)
from tiny_swarm_world.domain.preflight import HostPreparationResult, HostPreparationStatus


class WslHostPreparation(PortHostPreparation):
    def __init__(
        self,
        runner: PortWindowsCommandRunner,
        *,
        script_path: Path,
        config_path: Path,
        port_registry_path: Path,
        timeout_seconds: float = 120.0,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("WSL host preparation timeout must be positive.")
        self.runner = runner
        self.script_path = script_path
        self.config_path = config_path
        self.port_registry_path = port_registry_path
        self.timeout_seconds = timeout_seconds

    def prepare(self) -> HostPreparationResult:
        verification = self.runner.run(
            "verify",
            script_path=self.script_path,
            config_path=self.config_path,
            port_registry_path=self.port_registry_path,
            timeout_seconds=self.timeout_seconds,
        )
        if verification.timed_out or verification.interrupted:
            return self._result("prepare", "verify", verification)
        if verification.return_code == 0:
            return HostPreparationResult(
                "prepare",
                "wsl2",
                HostPreparationStatus.SUCCESS,
                "WSL2 host network preparation was already verified; no mutation was needed.",
                changed=False,
                verified=True,
                evidence={
                    "windows_action": "verify",
                    "preparation_path": "verified_noop",
                    "return_code": "0",
                    "timed_out": "false",
                    "interrupted": "false",
                },
            )
        return self._run("prepare", "refresh")

    def verify(self) -> HostPreparationResult:
        return self._run("verify", "verify")

    def cleanup(self) -> HostPreparationResult:
        return self._run("cleanup", "uninstall")

    def _run(self, operation: str, action: str) -> HostPreparationResult:
        result = self.runner.run(
            action,
            script_path=self.script_path,
            config_path=self.config_path,
            port_registry_path=self.port_registry_path,
            timeout_seconds=self.timeout_seconds,
        )
        return self._result(operation, action, result)

    def _result(
        self,
        operation: str,
        action: str,
        result: object,
    ) -> HostPreparationResult:
        interrupted = bool(getattr(result, "interrupted", False))
        timed_out = bool(getattr(result, "timed_out", False))
        return_code = getattr(result, "return_code", None)
        stdout = getattr(result, "stdout", "")
        stderr = getattr(result, "stderr", "")
        if interrupted:
            status = HostPreparationStatus.INTERRUPTED
        elif timed_out:
            status = HostPreparationStatus.TIMED_OUT
        elif return_code != 0:
            status = HostPreparationStatus.FAILED
        else:
            status = HostPreparationStatus.SUCCESS
        return HostPreparationResult(
            operation,
            "wsl2",
            status,
            _message(operation, status),
            changed=operation in {"prepare", "cleanup"} and status is HostPreparationStatus.SUCCESS,
            verified=status is HostPreparationStatus.SUCCESS,
            evidence={
                "windows_action": action,
                "return_code": str(return_code) if return_code is not None else "",
                "timed_out": str(timed_out).lower(),
                "interrupted": str(interrupted).lower(),
                "stdout_available": str(bool(stdout)).lower(),
                "stderr_available": str(bool(stderr)).lower(),
            },
        )


def _message(operation: str, status: HostPreparationStatus) -> str:
    if status is HostPreparationStatus.SUCCESS:
        return f"WSL2 host {operation} completed."
    if status is HostPreparationStatus.TIMED_OUT:
        return f"WSL2 host {operation} timed out before completion."
    if status is HostPreparationStatus.INTERRUPTED:
        return f"WSL2 host {operation} was interrupted."
    return f"WSL2 host {operation} failed."
