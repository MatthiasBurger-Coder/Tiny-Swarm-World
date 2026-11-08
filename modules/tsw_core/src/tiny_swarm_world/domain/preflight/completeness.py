"""Coverage and persistence metadata, independent of release acceptance."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class PreflightConstruction(StrEnum):
    CUSTOM = "CUSTOM"
    STANDARD_SETUP = "STANDARD_SETUP"


class SummaryPersistence(StrEnum):
    NOT_REQUESTED = "NOT_REQUESTED"
    MISSING_WRITER = "MISSING_WRITER"
    STORED = "STORED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PreflightCompleteness:
    construction: PreflightConstruction = PreflightConstruction.CUSTOM
    collaborators: Mapping[str, bool] = field(default_factory=dict)
    applicable_collaborators: tuple[str, ...] = ()
    invalid_checks: tuple[str, ...] = ()
    scope: str = "UNKNOWN"
    summary_persistence: SummaryPersistence = SummaryPersistence.NOT_REQUESTED

    def __post_init__(self) -> None:
        object.__setattr__(self, "collaborators", MappingProxyType(dict(self.collaborators)))

    @property
    def missing_collaborators(self) -> tuple[str, ...]:
        return tuple(name for name, available in self.collaborators.items() if not available)

    @property
    def collaborators_complete(self) -> bool:
        return bool(self.collaborators) and not self.missing_collaborators

    @property
    def qualification_complete(self) -> bool:
        return self.scope != "UNKNOWN" and not self.invalid_checks and all(
            self.collaborators.get(name, False) for name in self.applicable_collaborators
        )

    @property
    def evidence_complete(self) -> bool:
        return (self.collaborators_complete and not self.invalid_checks
                and self.summary_persistence is SummaryPersistence.STORED)

    def to_dict(self) -> dict[str, object]:
        return {
            "construction": self.construction.value,
            "collaborators": dict(self.collaborators),
            "missing_collaborators": list(self.missing_collaborators),
            "applicable_collaborators": list(self.applicable_collaborators),
            "collaborators_complete": self.collaborators_complete,
            "qualification_complete": self.qualification_complete,
            "invalid_checks": list(self.invalid_checks),
            "scope": self.scope,
            "summary_persistence": self.summary_persistence.value,
            "evidence_complete": self.evidence_complete,
            "release_evidence_acceptance": "NOT_EVALUATED",
        }
