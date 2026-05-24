from __future__ import annotations

import asyncio
from collections.abc import Iterable

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType
from tiny_swarm_world.application.ports.commands.port_command_workflow import PortCommandWorkflow
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


CommandConfigRef = tuple[str, dict[ParameterType, str] | None]


def verify_command_configs(
    command_workflow: PortCommandWorkflow,
    *,
    target_id: str,
    workflow_id: str,
    config_files: Iterable[str | CommandConfigRef],
) -> VerificationResult:
    checked_count = 0
    for item in config_files:
        if isinstance(item, tuple):
            config_file, parameter = item
        else:
            config_file = item
            parameter = None
        checked_count += 1
        result = command_workflow.verify_config_contract(
            config_file,
            parameter,
            workflow_id=workflow_id,
            target_id=target_id,
        )
        if result.status != VerificationStatus.VERIFIED:
            return result

    return VerificationResult(
        target_id=target_id,
        status=VerificationStatus.VERIFIED,
        message="Command-backed verification contracts are configured.",
        evidence={"phase": "pre_apply", "catalog_count": str(checked_count)},
    )


async def verify_command_execution(
    command_workflow: PortCommandWorkflow,
    *,
    target_id: str,
    workflow_id: str,
    config_file: str,
    max_attempts: int = 1,
    wait_seconds: float = 0,
) -> VerificationResult:
    last_exception: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await command_workflow.run_async(config_file, workflow_id=workflow_id)
        except Exception as exc:
            last_exception = exc
            if attempt < max_attempts:
                await asyncio.sleep(wait_seconds)
                continue
        else:
            return VerificationResult(
                target_id=target_id,
                status=VerificationStatus.VERIFIED,
                message="Post-apply verification command completed.",
                evidence={
                    "phase": "verify",
                    "config_file": config_file,
                    "attempt": str(attempt),
                },
            )

    exception_name = last_exception.__class__.__name__ if last_exception is not None else "UnknownError"
    return VerificationResult(
        target_id=target_id,
        status=VerificationStatus.FAILED_TO_VERIFY,
        message=f"Post-apply verification failed: {exception_name}",
        evidence={
            "phase": "verify",
            "config_file": config_file,
            "attempts": str(max_attempts),
        },
    )
