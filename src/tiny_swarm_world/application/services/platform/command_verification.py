from __future__ import annotations

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
