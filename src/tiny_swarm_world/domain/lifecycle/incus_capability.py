"""Closed, domain-only classification of Incus capability intent."""
from __future__ import annotations

from enum import Enum
import re


class IntentKind(Enum):
    """Explicit legacy or installation-scoped intent."""

    LEGACY_CLASSIC = "legacy_classic"
    INSTALLATION_SCOPED = "installation_scoped"


class CapabilityResult(Enum):
    """Closed classifications; none grants runtime host admission."""

    INVALID_INTENT = "invalid_intent"
    INVALID_VERSION = "invalid_version"
    UNSUPPORTED = "unsupported"
    LEGACY_CLASSIC = "legacy_classic"


SUPPORTED_VERSIONS: frozenset[str] = frozenset()
_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", re.ASCII)


def classify_incus_capability(intent: object, version: object = None) -> CapabilityResult:
    """Classify explicit intent without host access or support admission."""
    if type(intent) is not IntentKind:
        return CapabilityResult.INVALID_INTENT
    if intent is IntentKind.LEGACY_CLASSIC:
        return CapabilityResult.LEGACY_CLASSIC if version is None else CapabilityResult.INVALID_INTENT
    if type(version) is not str:
        return CapabilityResult.INVALID_VERSION
    try:
        if len(version) > 32 or _VERSION.fullmatch(version) is None:
            return CapabilityResult.INVALID_VERSION
    except Exception:
        return CapabilityResult.INVALID_VERSION
    return CapabilityResult.UNSUPPORTED
