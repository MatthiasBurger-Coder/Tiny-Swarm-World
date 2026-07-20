"""Resolve optional skill context without taking command-router authority."""

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class ActivationContext:
    """Inputs known after the command strand has already been selected."""

    command: str
    evidence: FrozenSet[str] = frozenset()
    approved_external_skills: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class ActivationDecision:
    """Context selection result; mandatory workflow controls are preserved."""

    selected_skills: tuple[str, ...]
    command: str
    gates_immutable: bool = True
    activated_count: int = 0
    rejected_count: int = 0


_CONDITIONAL_EVIDENCE = {
    "browser": "browser-module-present",
    "frontend-react": "verified-frontend-module",
}


def resolve_activation(
    context: ActivationContext,
    candidates: FrozenSet[str] = frozenset(),
) -> ActivationDecision:
    """Select only candidates justified by evidence or explicit approval.

    The resolver does not choose or rewrite the command strand and never
    returns workflow requirements, ordering, quality gates or stop conditions.
    """

    selected: list[str] = []
    rejected = 0
    for skill in sorted(candidates):
        required_evidence = _CONDITIONAL_EVIDENCE.get(skill)
        if required_evidence is not None and required_evidence not in context.evidence:
            rejected += 1
            continue
        if skill.startswith("external:") and skill not in context.approved_external_skills:
            rejected += 1
            continue
        selected.append(skill)
    return ActivationDecision(
        tuple(selected), context.command, True, len(selected), rejected
    )
