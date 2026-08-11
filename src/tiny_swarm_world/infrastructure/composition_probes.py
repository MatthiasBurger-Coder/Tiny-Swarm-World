"""Bounded, read-only probes used by infrastructure composition.

The probe module owns external observation mechanics. It never mutates live
infrastructure and returns the same typed verification evidence used by the
application workflows.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
import time
from pathlib import Path

import requests

from tiny_swarm_world.domain.deployment import ServiceStackContract
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EndpointReadinessCheck:
    def __init__(
        self,
        service_stack: ServiceStackContract,
        *,
        verification_target_id: str | None = None,
        max_attempts: int = 60,
        wait_seconds: int = 5,
        timeout_seconds: int = 5,
        session: requests.Session | None = None,
    ) -> None:
        if max_attempts <= 0:
            raise ValueError("Endpoint readiness attempts must be positive.")
        if wait_seconds < 0:
            raise ValueError("Endpoint readiness wait seconds must not be negative.")
        if timeout_seconds <= 0:
            raise ValueError("Endpoint readiness timeout must be positive.")
        self.service_stack = service_stack
        self.verification_target_id = verification_target_id or service_stack.service_readiness_target_id
        self.deployment_target_id = self.verification_target_id
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self._verification = VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.BLOCKED,
            message="Endpoint readiness has not run yet.",
            evidence={
                "phase": "apply",
                "reason": "readiness_not_run",
                "stack_name": service_stack.stack_name,
            },
        )

    async def run(self) -> None:
        self._verification = await self._probe_until_ready_async(phase="apply")

    def verify(self) -> VerificationResult:
        if self._verification.status is not VerificationStatus.BLOCKED:
            return self._verification
        return self._probe_until_ready(phase="verify")

    async def verify_async(self) -> VerificationResult:
        if self._verification.status is not VerificationStatus.BLOCKED:
            return self._verification
        return await self._probe_until_ready_async(phase="verify")

    async def _probe_until_ready_async(self, *, phase: str) -> VerificationResult:
        if not self.service_stack.endpoints:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="Endpoint readiness has no configured endpoints.",
                evidence=_endpoint_readiness_evidence(self.service_stack, {}, phase=phase, attempt=0),
            )
        last_statuses: dict[str, str] = {}
        for attempt in range(1, self.max_attempts + 1):
            last_statuses = {}
            for endpoint in self.service_stack.endpoints:
                last_statuses[endpoint.name] = await asyncio.to_thread(
                    _endpoint_status,
                    self.session,
                    endpoint.url,
                    timeout_seconds=self.timeout_seconds,
                )
            if all(_endpoint_status_ready(status) for status in last_statuses.values()):
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.VERIFIED,
                    message="Service endpoints are reachable.",
                    evidence=_endpoint_readiness_evidence(
                        self.service_stack,
                        last_statuses,
                        phase=phase,
                        attempt=attempt,
                    ),
                )
            if attempt < self.max_attempts:
                await asyncio.sleep(self.wait_seconds)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Service endpoints did not become reachable in time.",
            evidence=_endpoint_readiness_evidence(
                self.service_stack,
                last_statuses,
                phase=phase,
                attempt=self.max_attempts,
            ),
        )

    def _probe_until_ready(self, *, phase: str) -> VerificationResult:
        if not self.service_stack.endpoints:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.BLOCKED,
                message="Endpoint readiness has no configured endpoints.",
                evidence=_endpoint_readiness_evidence(self.service_stack, {}, phase=phase, attempt=0),
            )
        last_statuses: dict[str, str] = {}
        for attempt in range(1, self.max_attempts + 1):
            last_statuses = {
                endpoint.name: _endpoint_status(
                    self.session,
                    endpoint.url,
                    timeout_seconds=self.timeout_seconds,
                )
                for endpoint in self.service_stack.endpoints
            }
            if all(_endpoint_status_ready(status) for status in last_statuses.values()):
                return VerificationResult(
                    target_id=self.verification_target_id,
                    status=VerificationStatus.VERIFIED,
                    message="Service endpoints are reachable.",
                    evidence=_endpoint_readiness_evidence(
                        self.service_stack,
                        last_statuses,
                        phase=phase,
                        attempt=attempt,
                    ),
                )
            if attempt < self.max_attempts:
                time.sleep(self.wait_seconds)
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Service endpoints did not become reachable in time.",
            evidence=_endpoint_readiness_evidence(
                self.service_stack,
                last_statuses,
                phase=phase,
                attempt=self.max_attempts,
            ),
        )


def _endpoint_status(
    session: requests.Session,
    url: str,
    *,
    timeout_seconds: int,
) -> str:
    try:
        response = session.get(url, timeout=timeout_seconds, allow_redirects=False)
    except requests.Timeout:
        return "timeout"
    except requests.RequestException:
        return "connection_error"
    return f"http_{response.status_code}"


def _endpoint_status_ready(status: str) -> bool:
    if not status.startswith("http_"):
        return False
    try:
        status_code = int(status.removeprefix("http_"))
    except ValueError:
        return False
    return 100 <= status_code < 500


def _endpoint_readiness_evidence(
    service_stack: ServiceStackContract,
    statuses: dict[str, str],
    *,
    phase: str,
    attempt: int,
) -> dict[str, str]:
    return {
        "attempt": str(attempt),
        "endpoint_statuses": ",".join(
            f"{name}={status}" for name, status in sorted(statuses.items())
        ),
        "evidence_kind": "service_endpoint_http",
        "phase": phase,
        "stack_name": service_stack.stack_name,
    }


def _wsl_lxc_lifecycle_capability_available() -> bool:
    return (
        _wsl_unprivileged_userns_clone_available()
        and Path("/sys/fs/cgroup/cgroup.controllers").exists()
        and Path("/proc/self/uid_map").exists()
    )


def _wsl_unprivileged_userns_clone_available(
    path: Path = Path("/proc/sys/kernel/unprivileged_userns_clone"),
) -> bool:
    if not path.exists():
        return True
    return _linux_text_file_equals(path, "1")


def _linux_text_file_equals(path: Path, expected: str) -> bool:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip() == expected
    except OSError:
        return False


def _lxc_reachable_host_ip() -> str:
    for interface_name in ("incusbr0",):
        address = _host_ipv4_for_interface(interface_name)
        if address:
            return address
    return ""


def _host_ipv4_for_interface(interface_name: str) -> str:
    try:
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show", "dev", interface_name],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    match = re.search(r"\binet\s+(?P<address>\d+\.\d+\.\d+\.\d+)/", result.stdout)
    return match.group("address") if match else ""
