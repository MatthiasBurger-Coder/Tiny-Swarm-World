"""Pure aggregation of explicit requested-work evidence and classified failures."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from tiny_swarm_world.application.ports.operation_result import (
    OperationError, OperationFailure, OperationOutcome, OperationResult,
)


def failure_from_exception(error: Exception, operation: str, component: str) -> OperationFailure:
    if isinstance(error, OperationError):
        return error.failure
    return OperationFailure.for_cause(operation, component, "unexpected_failure")


def failures_to_evidence(failures: Sequence[OperationFailure]) -> dict[str, str]:
    return {
        f"failure_{index}_{key}": value
        for index, failure in enumerate(failures, 1)
        for key, value in failure.to_dict().items()
    }


def failures_from_evidence(
    evidence: Mapping[str, str], *,
    allowed_origins: frozenset[tuple[str, str]] = frozenset(),
    fallback_operation: str = "operation.check", fallback_component: str = "application",
) -> tuple[OperationFailure, ...]:
    fields = {"operation", "component", "cause", "recoverability", "recommended_action"}
    indexed: dict[int, set[str]] = {}
    for key in evidence:
        if not re.match(r"failure_[0-9]", key):
            continue
        match = re.fullmatch(r"failure_([1-9][0-9]{0,3})_([a-z_]+)", key)
        if match is None or match.group(2) not in fields:
            raise ValueError("Structured failure fields are invalid.")
        indexed.setdefault(int(match.group(1)), set()).add(match.group(2))
    if any(value != fields for value in indexed.values()):
        raise ValueError("Indexed failure context is incomplete.")
    indices = sorted(indexed)
    if indices and indices != list(range(1, len(indices) + 1)):
        raise ValueError("Structured failure indices must be contiguous.")
    prefixes = [f"failure_{index}_" for index in indices]
    if any("failure_" + field in evidence for field in fields) and "failure_cause" not in evidence:
        raise ValueError("Legacy failure context is incomplete.")
    if "failure_cause" in evidence:
        prefixes.insert(0, "failure_")
    failures: list[OperationFailure] = []
    for prefix in prefixes:
        if prefix != "failure_" and any(prefix + key not in evidence for key in ("operation", "component", "recoverability", "recommended_action")):
            raise ValueError("Indexed failure context is incomplete.")
        origin = (fallback_operation, fallback_component) if prefix == "failure_" else (
            evidence[prefix + "operation"], evidence[prefix + "component"],
        )
        if prefix != "failure_" and origin not in allowed_origins:
            raise ValueError("Failure origin is not declared by the caller.")
        failure = OperationFailure.for_cause(*origin, evidence[prefix + "cause"])
        for field in ("recoverability", "recommended_action"):
            if prefix + field in evidence and evidence[prefix + field] != failure.to_dict()[field]:
                raise ValueError("Failure evidence conflicts with its declared cause.")
        failures.append(failure)
    return tuple(failures)


def progress_to_evidence(result: OperationResult) -> dict[str, str]:
    evidence = {"operation_progress_version": "1", **failures_to_evidence(result.failures)}
    for field, values in (
        ("completed", result.completed_operations),
        ("pending", result.pending_operations),
        ("uncertain", result.uncertain_operations),
    ):
        evidence[f"operation_{field}_count"] = str(len(values))
        evidence.update({f"operation_{field}_{index}": value for index, value in enumerate(values, 1)})
    return evidence


def progress_from_evidence(
    evidence: Mapping[str, str], field: str, *, allowed_operations: frozenset[str],
) -> tuple[str, ...]:
    if "operation_progress_version" not in evidence:
        if any(key.startswith("operation_") for key in evidence):
            raise ValueError("Operation progress version is missing.")
        return ()
    if evidence["operation_progress_version"] != "1":
        raise ValueError("Operation progress version is unsupported.")
    if field not in {"completed", "pending", "uncertain"}:
        raise ValueError("Unknown operation progress field.")
    raw_count = evidence.get(f"operation_{field}_count", "")
    if not raw_count.isdecimal() or len(raw_count) > 4:
        raise ValueError("Operation progress count is invalid.")
    count = int(raw_count)
    keys = {f"operation_{field}_{index}" for index in range(1, count + 1)}
    actual_keys = {key for key in evidence if key.startswith(f"operation_{field}_") and not key.endswith("_count")}
    if keys != actual_keys:
        raise ValueError("Operation progress fields are incomplete or inconsistent.")
    values = tuple(evidence[f"operation_{field}_{index}"] for index in range(1, count + 1))
    if any(value not in allowed_operations for value in values):
        raise ValueError("Operation progress is outside the caller's requested plan.")
    OperationResult(OperationOutcome.SUCCESS, completed_operations=values)
    return values


def aggregate_operation(
    outcome: OperationOutcome,
    *,
    completed: Sequence[str] = (),
    pending: Sequence[str] = (),
    uncertain: Sequence[str] = (),
    failures: Sequence[OperationFailure] = (),
    rollback_verified: bool = False,
) -> OperationResult:
    completed_values = tuple(completed)
    uncertain_values = tuple(uncertain)
    pending_values = tuple(pending)
    if outcome not in (OperationOutcome.SUCCESS, OperationOutcome.ROLLED_BACK):
        if completed_values:
            outcome = OperationOutcome.PARTIAL
        elif uncertain_values:
            outcome = OperationOutcome.FAILED
    return OperationResult(
        outcome, tuple(failures), completed_values, pending_values, uncertain_values,
        rollback_verified=rollback_verified,
    )
