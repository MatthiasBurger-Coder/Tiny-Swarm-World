"""Compatibility export for the side-effect-free evidence sanitizer."""

from tiny_swarm_world.domain.sanitized_evidence import (
    UNSAFE_EVIDENCE_KEY_PARTS,
    sanitized_evidence,
)

__all__ = ["UNSAFE_EVIDENCE_KEY_PARTS", "sanitized_evidence"]
