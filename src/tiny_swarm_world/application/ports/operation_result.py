"""Immutable, safe operation outcomes shared by ports and workflow consumers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class OperationOutcome(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"
    REFUSED = "refused"


class Recoverability(str, Enum):
    RECOVERABLE = "recoverable"
    NONRECOVERABLE = "nonrecoverable"
    UNKNOWN = "unknown"


# Guidance describes a human decision; it never grants permission to retry.
_FAILURE_CATALOGUE = MappingProxyType({
    "launch_executable_missing": (Recoverability.NONRECOVERABLE, "Install the required executable and retry after prerequisites pass."),
    "launch_permission_denied": (Recoverability.NONRECOVERABLE, "Check executable permissions and rerun prerequisite checks."),
    "launch_os_error": (Recoverability.UNKNOWN, "Inspect local execution prerequisites before retrying."),
    "process_timeout": (Recoverability.UNKNOWN, "Inspect operation state before retrying; effects may be incomplete."),
    "process_exit_failed": (Recoverability.UNKNOWN, "Inspect redacted evidence and correct the failed operation."),
    "filesystem_error": (Recoverability.UNKNOWN, "Check storage access and available space before retrying."),
    "configuration_invalid": (Recoverability.NONRECOVERABLE, "Correct the selected configuration and rerun validation."),
    "state_invalid": (Recoverability.NONRECOVERABLE, "Preserve invalid recovery state for diagnosis before correcting it."),
    "observation_unavailable": (Recoverability.UNKNOWN, "Refresh observed state before deciding whether to retry."),
    "observation_changed": (Recoverability.UNKNOWN, "Refresh observed state before deciding whether to retry."),
    "dependency_unavailable": (Recoverability.UNKNOWN, "Check service readiness and connection settings."),
    "request_timeout": (Recoverability.UNKNOWN, "Inspect service state and connectivity before retrying; effects may be incomplete."),
    "registry_rate_limited": (Recoverability.NONRECOVERABLE, "Configure registry authentication or an approved mirror before retrying."),
    "request_failed": (Recoverability.UNKNOWN, "Check service readiness and connection settings."),
    "verification_failed": (Recoverability.UNKNOWN, "Inspect verification evidence and actual target state."),
    "refused": (Recoverability.NONRECOVERABLE, "Review required consent before rerunning."),
    "blocked": (Recoverability.NONRECOVERABLE, "Review required prerequisites before rerunning."),
    "unexpected_failure": (Recoverability.UNKNOWN, "Inspect redacted diagnostic evidence; do not assume retry is safe."),
})
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_.:-]{0,127}\Z")


def _validate_identifier(value: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError("Operation identifiers must be bounded lowercase identifiers.")


@dataclass(frozen=True)
class OperationFailure:
    operation: str
    component: str
    cause: str
    recoverability: Recoverability
    recommended_action: str

    def __post_init__(self) -> None:
        _validate_identifier(self.operation)
        _validate_identifier(self.component)
        if not isinstance(self.cause, str) or self.cause not in _FAILURE_CATALOGUE:
            raise ValueError("Failure cause must belong to the declared catalogue.")
        if not isinstance(self.recoverability, Recoverability):
            raise TypeError("Recoverability must be explicit.")
        if (self.recoverability, self.recommended_action) != _FAILURE_CATALOGUE[self.cause]:
            raise ValueError("Failure guidance must match the declared cause catalogue.")

    @classmethod
    def for_cause(cls, operation: str, component: str, cause: str) -> OperationFailure:
        if not isinstance(cause, str) or cause not in _FAILURE_CATALOGUE:
            raise ValueError("Failure cause must belong to the declared catalogue.")
        recoverability, action = _FAILURE_CATALOGUE[cause]
        return cls(operation, component, cause, recoverability, action)

    def to_dict(self) -> dict[str, str]:
        return {
            "operation": self.operation,
            "component": self.component,
            "cause": self.cause,
            "recoverability": self.recoverability.value,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True)
class OperationResult:
    outcome: OperationOutcome
    failures: tuple[OperationFailure, ...] = ()
    completed_operations: tuple[str, ...] = ()
    pending_operations: tuple[str, ...] = ()
    uncertain_operations: tuple[str, ...] = ()
    rollback_verified: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, OperationOutcome):
            raise TypeError("Outcome must be explicit.")
        if type(self.rollback_verified) is not bool:
            raise TypeError("Rollback verification must be boolean.")
        if not isinstance(self.failures, tuple) or any(
            not isinstance(item, OperationFailure) for item in self.failures
        ):
            raise TypeError("Failures must be an immutable tuple of structured failures.")
        seen: set[str] = set()
        for operations in (self.completed_operations, self.pending_operations, self.uncertain_operations):
            if not isinstance(operations, tuple):
                raise TypeError("Operation evidence must be an immutable tuple.")
            for operation in operations:
                _validate_identifier(operation)
                if operation in seen:
                    raise ValueError("Operation evidence must be unique and disjoint.")
                seen.add(operation)
        self._validate_outcome()

    def _validate_outcome(self) -> None:
        incomplete = bool(self.pending_operations or self.uncertain_operations)
        if self.outcome == OperationOutcome.SUCCESS and (self.failures or incomplete):
            raise ValueError("Success cannot contain failures or incomplete work.")
        if self.outcome in (OperationOutcome.FAILED, OperationOutcome.PARTIAL) and not self.failures:
            raise ValueError("Failed and partial outcomes require structured failures.")
        if self.outcome == OperationOutcome.FAILED and self.completed_operations:
            raise ValueError("Failed cannot erase confirmed completed work; use partial.")
        if self.outcome == OperationOutcome.PARTIAL and not (self.completed_operations and incomplete):
            raise ValueError("Partial requires confirmed completion and incomplete requested work.")
        if self.outcome in (OperationOutcome.BLOCKED, OperationOutcome.REFUSED) and (
            self.completed_operations or self.uncertain_operations
        ):
            raise ValueError("Blocked and refused describe requests before execution.")
        if self.rollback_verified != (self.outcome == OperationOutcome.ROLLED_BACK):
            raise ValueError("Only observed rolled-back outcomes have verified rollback.")
        if self.outcome == OperationOutcome.ROLLED_BACK and incomplete:
            raise ValueError("Verified rollback cannot contain unresolved work.")

    def to_dict(self) -> dict[str, object]:
        return {
            "outcome": self.outcome.value,
            "failures": [failure.to_dict() for failure in self.failures],
            "completed_operations": list(self.completed_operations),
            "pending_operations": list(self.pending_operations),
            "uncertain_operations": list(self.uncertain_operations),
            "rollback_verified": self.rollback_verified,
        }


class OperationError(Exception):
    """Declared port failure containing only classified, safe public context."""

    def __init__(self, failure: OperationFailure):
        if not isinstance(failure, OperationFailure):
            raise TypeError("Port errors require a structured failure.")
        self.failure = failure
        super().__init__(f"{failure.operation}: {failure.cause}. {failure.recommended_action}")
