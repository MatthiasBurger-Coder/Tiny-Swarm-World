"""Closed application request and non-admitting migration result."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode


class MigrationAdmissionStatus(Enum):
    BLOCKED_UNKNOWN = "BLOCKED_UNKNOWN"
    BLOCKED_UNSUPPORTED = "BLOCKED_UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class MigrationAdmissionRequest:
    version: str
    exposure: SwaggerMode
    listen_address: str


@dataclass(frozen=True, slots=True)
class MigrationAdmissionResult:
    status: MigrationAdmissionStatus
    applied: bool = field(default=False, init=False)
    qualified: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self.status) is not MigrationAdmissionStatus:
            raise ValueError("Invalid migration admission status.")
