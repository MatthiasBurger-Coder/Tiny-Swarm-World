from __future__ import annotations

from dataclasses import dataclass


PLATFORM_INIT_WORKFLOW_ID = "platform:init"
PLATFORM_RECONCILE_WORKFLOW_ID = "platform:reconcile"


@dataclass(frozen=True)
class VerificationProbeContract:
    probe_id: str
    allowed_workflows: frozenset[str]


KNOWN_VERIFICATION_PROBES: dict[str, VerificationProbeContract] = {
    "probe:platform:vm-created": VerificationProbeContract(
        probe_id="probe:platform:vm-created",
        allowed_workflows=frozenset({PLATFORM_INIT_WORKFLOW_ID}),
    ),
    "probe:platform:network-addresses": VerificationProbeContract(
        probe_id="probe:platform:network-addresses",
        allowed_workflows=frozenset(
            {PLATFORM_INIT_WORKFLOW_ID, PLATFORM_RECONCILE_WORKFLOW_ID}
        ),
    ),
    "probe:platform:netplan-applied": VerificationProbeContract(
        probe_id="probe:platform:netplan-applied",
        allowed_workflows=frozenset({PLATFORM_INIT_WORKFLOW_ID}),
    ),
    "probe:platform:docker-installed": VerificationProbeContract(
        probe_id="probe:platform:docker-installed",
        allowed_workflows=frozenset({PLATFORM_INIT_WORKFLOW_ID}),
    ),
    "probe:platform:swarm-ready": VerificationProbeContract(
        probe_id="probe:platform:swarm-ready",
        allowed_workflows=frozenset({PLATFORM_INIT_WORKFLOW_ID}),
    ),
    "probe:platform:vm-network-inventory": VerificationProbeContract(
        probe_id="probe:platform:vm-network-inventory",
        allowed_workflows=frozenset({PLATFORM_RECONCILE_WORKFLOW_ID}),
    ),
}


def get_verification_probe_contract(probe_id: str) -> VerificationProbeContract | None:
    return KNOWN_VERIFICATION_PROBES.get(probe_id)


def is_probe_allowed_for_workflow(probe_id: str, workflow_id: str) -> bool:
    contract = get_verification_probe_contract(probe_id)
    return contract is not None and workflow_id in contract.allowed_workflows
