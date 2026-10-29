"""Redacted closed types for the isolated versioned draft repository."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Protocol

from tiny_swarm_world.domain.lifecycle.manifest_v2_record import UnadoptedV2Record
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode


class TokenKind(Enum):
    ABSENT = "ABSENT"
    PRESENT = "PRESENT"


@dataclass(frozen=True, slots=True, repr=False)
class CasToken:
    kind: TokenKind
    digest: str | None = None

    def __post_init__(self) -> None:
        if (type(self.kind) is not TokenKind
                or (self.kind is TokenKind.ABSENT and self.digest is not None)
                or (self.kind is TokenKind.PRESENT and
                    (type(self.digest) is not str or re.fullmatch(r"[0-9a-f]{64}", self.digest) is None))):
            raise ValueError("Invalid token.")

    def __repr__(self) -> str:
        return "<CasToken redacted>"

    __str__ = __repr__


ABSENT_TOKEN = CasToken(TokenKind.ABSENT)


def _valid_token(value: object, kind: TokenKind) -> bool:
    if type(value) is not CasToken or value.kind is not kind:
        return False
    try:
        CasToken(value.kind, value.digest)
        return True
    except ValueError:
        return False


class ReadStatus(Enum):
    ABSENT = "ABSENT"
    PRESENT = "PRESENT"
    BLOCKED = "BLOCKED"


class WriteStatus(Enum):
    SUCCESS = "SUCCESS"
    CONFLICT = "CONFLICT"
    BLOCKED = "BLOCKED"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True, slots=True, repr=False)
class ReadResult:
    status: ReadStatus
    record: InstallationManifest | UnadoptedV2Record | None = None
    token: CasToken | None = None

    def __post_init__(self) -> None:
        if (type(self.status) is not ReadStatus
                or (self.status is ReadStatus.ABSENT and (self.record is not None or not _valid_token(self.token, TokenKind.ABSENT)))
                or (self.status is ReadStatus.PRESENT and
                    (type(self.record) not in {InstallationManifest, UnadoptedV2Record}
                     or not _valid_token(self.token, TokenKind.PRESENT)))
                or (self.status is ReadStatus.BLOCKED and (self.record is not None or self.token is not None))):
            raise ValueError("Invalid read result.")

    def __repr__(self) -> str:
        return "<ReadResult redacted>"

    __str__ = __repr__


@dataclass(frozen=True, slots=True, repr=False)
class WriteResult:
    status: WriteStatus
    token: CasToken | None = None

    def __post_init__(self) -> None:
        if (type(self.status) is not WriteStatus
                or (self.status is WriteStatus.SUCCESS and
                    not _valid_token(self.token, TokenKind.PRESENT))
                or (self.status is not WriteStatus.SUCCESS and self.token is not None)):
            raise ValueError("Invalid write result.")

    def __repr__(self) -> str:
        return "<WriteResult redacted>"

    __str__ = __repr__


class VersionedManifestRepository(Protocol):
    def read(self, catalog: ComponentCatalog, exposure: SwaggerMode, listen_address: str) -> ReadResult: ...
    def compare_and_swap(self, record: UnadoptedV2Record, expected: CasToken, catalog: ComponentCatalog,
                         exposure: SwaggerMode, listen_address: str) -> WriteResult: ...
