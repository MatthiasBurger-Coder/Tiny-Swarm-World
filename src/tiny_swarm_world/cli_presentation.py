"""Pure CLI result formatting and presentation helpers."""

import json
import os
from argparse import Namespace
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from pathlib import Path

from tiny_swarm_world.application.ports.operation_result import OperationResult
from tiny_swarm_world.application.services.artifacts import ArtifactWorkflowResult
from tiny_swarm_world.application.services.deployment import DeploymentWorkflowResult
from tiny_swarm_world.application.services.setup import SetupWorkflowResult
from tiny_swarm_world.application.services.platform.workflow.results import PlatformWorkflowResult
from tiny_swarm_world.application.services.setup.installation_plan import SetupInstallationPlan
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind, HostEnvironmentReport
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.domain.preflight import PreflightResult

WorkflowResult = PlatformWorkflowResult | ArtifactWorkflowResult | DeploymentWorkflowResult | SetupWorkflowResult


def render_setup_installation_plan(
    plan: SetupInstallationPlan,
    *,
    requested_provider: str,
    preferred_backend: ManagedLxcBackend | None,
) -> None:
    print()
    print("Tiny Swarm World guided installation")
    print("Target: local Linux/WSL LXC-native Docker Swarm")
    print(f"Default node provider: {requested_provider}")
    print(f"Managed backend: {preferred_backend.value if preferred_backend else 'Incus'}")
    print("Provider readiness: checked before platform mutation")
    print(f"Service profile: {plan.service_profile.value}")
    print("Platform:")
    print("- swarm-manager: Docker Swarm manager")
    print("- swarm-worker-1: Docker Swarm worker")
    print("- swarm-worker-2: Docker Swarm worker")
    print("Installation phases:")
    for phase in plan.phase_names:
        print(f"- {phase}")
    print("Services:")
    for service in plan.services:
        names = ", ".join(service.compose_service_names) or "not declared"
        ports = ", ".join(str(port) for port in service.published_ports) or "no published port"
        print(
            f"- {service.name}: stack {service.stack_name}, "
            f"source infra/config/compose/{service.stack_name}/docker-compose.yml, "
            f"compose service(s) {names}, published port(s) {ports}"
        )
    print()

def _host_detection_payload(report: HostEnvironmentReport) -> dict[str, object]:
    return {
        **report.to_dict(),
        "live_readiness_verified": False,
    }


def _print_host_environment_summary(report: HostEnvironmentReport) -> None:
    print("Host environment")
    print(f"Type: {report.environment.value}")
    print(f"Distribution: {report.distribution}")
    print(f"Kernel release: {report.kernel_release}")
    if report.environment is HostEnvironmentKind.NATIVE_LINUX:
        windows_interop = "not applicable"
    else:
        windows_interop = (
            "available" if report.windows_interop_available else "unavailable"
        )
    print(f"Windows interop: {windows_interop}")
    print(f"Supported: {'yes' if report.supported else 'no'}")
    print(f"Setup path: {report.setup_path.value}")
    print("Live readiness verified: no")
    if report.remediation:
        print("Remediation:")
        for item in report.remediation:
            print(f"- {item}")


def _workflow_result_to_dict(result: WorkflowResult) -> dict[str, object]:
    if isinstance(result, ArtifactWorkflowResult | DeploymentWorkflowResult | SetupWorkflowResult):
        return result.to_dict()
    return result.to_dict()


def _emit_workflow_result(result: WorkflowResult, args: Namespace) -> None:
    if _should_emit_json(args):
        _emit_json_payload(_workflow_result_to_dict(result))
        return
    if isinstance(result, SetupWorkflowResult):
        _print_setup_installation_summary(result)
        return
    _print_workflow_summary(result)


def _emit_json_payload(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _workflow_status_value(result: WorkflowResult) -> str:
    status = result.status
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


def _should_emit_json(args: Namespace) -> bool:
    if bool(args.json):
        return True
    return os.environ.get("TSW_DEBUG_JSON", "").strip().lower() == "true"


def _print_blocked_workflow_summary(payload: dict[str, object]) -> None:
    print()
    print(f"Workflow: {payload['workflow']}")
    print(f"Status: {payload['status']}")
    print(f"Message: {payload['message']}")


def _print_workflow_summary(result: WorkflowResult) -> None:
    for line in _format_workflow_summary(result):
        print(line)


def _format_workflow_summary(result: WorkflowResult) -> tuple[str, ...]:
    lines = [
        "",
        f"Workflow: {_workflow_name(result)}",
        f"Status: {_workflow_status_value(result)}",
        f"Executed: {'yes' if result.executed else 'no'}",
    ]
    message = getattr(result, "message", "")
    if message:
        lines.append(f"Message: {_console_text(message)}")
    reason = getattr(result, "reason", "")
    if reason:
        lines.append(f"Reason: {_console_text(reason)}")
    verification_results = getattr(result, "verification_results", ())
    if verification_results:
        lines.extend(_format_verification_summary(verification_results))
    lines.extend(_format_operation_summary(getattr(result, "operation_result", None)))
    return tuple(lines)


def _format_operation_summary(result: OperationResult | None) -> tuple[str, ...]:
    """Render validated operation context without performing recommended actions."""
    if result is None:
        return ()
    lines = [f"Operation outcome: {result.outcome.value}"]
    for label, operations in (
        ("Completed operations", result.completed_operations),
        ("Pending operations", result.pending_operations),
        ("Uncertain operations", result.uncertain_operations),
    ):
        if operations:
            lines.append(f"{label}: {', '.join(operations)}")
    if result.rollback_verified:
        lines.append("Rollback verified: yes")
    for failure in result.failures:
        lines.extend((
            f"Failure: {failure.operation} ({failure.component})",
            f"  Cause: {failure.cause}",
            f"  Recoverability: {failure.recoverability.value}",
            f"  Recommended action: {failure.recommended_action}",
        ))
    return tuple(lines)


def _format_verification_summary(
    verification_results: Sequence[object],
    *,
    indent: str = "",
) -> tuple[str, ...]:
    lines = [
        f"{indent}Verification counts: {_format_status_counts(verification_results)}",
        f"{indent}Verification summary:",
    ]
    for verification in verification_results:
        target_id = _console_text(getattr(verification, "target_id", "unknown"))
        status = _console_enum(getattr(verification, "status", "unknown"))
        lines.append(f"{indent}- {target_id}: {status}")
        evidence = getattr(verification, "evidence", {})
        if evidence:
            lines.append(f"{indent}  Evidence:")
            for key, value in sorted(evidence.items()):
                lines.append(
                    f"{indent}  - {key}: {_safe_console_value(value)}"
                )
    return tuple(lines)


def _workflow_name(result: WorkflowResult) -> str:
    workflow_name = getattr(result, "workflow_name", None)
    if workflow_name:
        return _console_text(workflow_name)
    return str(_workflow_result_to_dict(result).get("workflow", "workflow"))


def _print_preflight_summary(result: PreflightResult, *, live: bool = False) -> None:
    print()
    print(f"Preflight summary: {result.status}")
    if result.passed:
        if live:
            print("Preflight checks passed; provider readiness is checked by the platform guard.")
        else:
            print("Static checks passed; this does not claim live provider readiness.")
        return

    if result.resource_gated:
        print("Only resource-gated checks failed. Use a larger host or a smaller setup profile.")
    else:
        print("Fix the mandatory blockers before live setup.")

    for check in result.failed_checks:
        print(f"- {check.check_id}: {check.message}")
        if check.remediation and check.remediation != "None":
            print(f"  Action: {check.remediation}")


def _print_setup_installation_summary(result: SetupWorkflowResult) -> None:
    for line in _format_setup_installation_summary(result):
        print(line)


def _format_setup_installation_summary(
    result: SetupWorkflowResult,
) -> tuple[str, ...]:
    lines = [
        "",
        "Setup summary:",
        f"Workflow: {result.workflow_name}",
        f"Phases: {len(result.phase_results)}",
        f"Status counts: {_format_phase_status_counts(result.phase_results)}",
        f"Phase groups: {len(result.phase_group_results)}",
    ]
    if result.phase_group_results:
        lines.append("Phase group summary:")
        for group in result.phase_group_results:
            phase_names = ", ".join(group.phase_names) or "none"
            lines.append(
                f"- {group.group_id}: {group.status} "
                f"(phases={phase_names}; max-concurrency={group.maximum_concurrency}; "
                f"duration={group.duration_seconds:.3f}s)"
            )
    lines.append("Setup phase summary:")
    for phase in result.phase_results:
        lines.append(f"- {phase.name}: {phase.status}")
        lines.extend(_format_setup_phase_diagnostics(phase.result))
    if result.message:
        lines.append(f"Message: {_console_text(result.message)}")
    if result.reason:
        lines.append(f"Reason: {_console_text(result.reason)}")
    lines.extend(_format_operation_summary(result.operation_result))
    lines.append(f"Final setup status: {result.status.value}")
    lines.append("")
    return tuple(lines)


def _format_setup_phase_diagnostics(phase_result: object) -> tuple[str, ...]:
    if isinstance(phase_result, PreflightResult):
        if not phase_result.failed_checks:
            return ()
        lines = ["  Failed preflight checks:"]
        for check in phase_result.failed_checks:
            lines.append(
                f"  - {check.check_id}: {_console_text(check.message)}"
            )
            if check.remediation and check.remediation != "None":
                lines.append(f"    Action: {_console_text(check.remediation)}")
        return tuple(lines)
    if isinstance(
        phase_result,
        PlatformWorkflowResult | ArtifactWorkflowResult | DeploymentWorkflowResult,
    ):
        if _workflow_status_value(phase_result) in {"completed", "passed", "verified"}:
            return ()
        return _format_setup_nested_workflow_diagnostics(phase_result)
    return ()


def _print_setup_nested_workflow_diagnostics(result: WorkflowResult) -> None:
    for line in _format_setup_nested_workflow_diagnostics(result):
        print(line)


def _format_setup_nested_workflow_diagnostics(
    result: WorkflowResult,
) -> tuple[str, ...]:
    lines = [f"  Workflow: {_workflow_name(result)}"]
    message = getattr(result, "message", "")
    if message:
        lines.append(f"  Message: {_console_text(message)}")
    reason = getattr(result, "reason", "")
    if reason:
        lines.append(f"  Reason: {_console_text(reason)}")
    verification_results = getattr(result, "verification_results", ())
    if not verification_results:
        return tuple(lines)
    lines.extend(_format_verification_summary(verification_results, indent="  "))
    return tuple(lines)


def _format_phase_status_counts(phase_results: Sequence[object]) -> str:
    return _format_status_counts(
        (getattr(phase, "status", "unknown") for phase in phase_results)
    )


def _format_status_counts(values: Iterable[object]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        status = _console_enum(getattr(value, "status", value))
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(
        f"{status}={count}" for status, count in sorted(counts.items())
    ) or "none"


def _console_enum(value: object) -> str:
    if isinstance(value, Enum):
        return _console_text(value.value)
    return _console_text(value)


def _console_text(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return " ".join(text.split())


def _safe_console_value(value: object) -> str:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return _console_text(value.value)
    if isinstance(value, Mapping):
        return "structured value persisted to evidence"
    if isinstance(value, (list, tuple, set, frozenset)):
        return f"{len(value)} item(s) persisted to evidence"
    if isinstance(value, str):
        text = _console_text(value)
        if (
            text.startswith(("{", "["))
            and text.endswith(("}", "]"))
        ):
            return "structured value persisted to evidence"
        return text
    if isinstance(value, (bool, int, float)):
        return str(value)
    return f"{type(value).__name__} persisted to evidence"
