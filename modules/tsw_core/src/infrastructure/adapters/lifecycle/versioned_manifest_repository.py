"""Isolated staging-only, byte-hash CAS repository for unadopted v2 drafts."""
from __future__ import annotations

import hashlib
from pathlib import Path

from tiny_swarm_world.application.ports.lifecycle.versioned_manifest import (
    ABSENT_TOKEN, CasToken, ReadResult, ReadStatus, TokenKind, WriteResult, WriteStatus,
)
from tiny_swarm_world.domain.lifecycle.manifest_v2_record import UnadoptedV2Record, encode_v2_record, validate_v2_wire
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog, InstallationManifest
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode
from tiny_swarm_world.infrastructure.adapters.lifecycle import versioned_manifest_fs as fs
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import decode_manifest
from tiny_swarm_world.infrastructure.adapters.lifecycle.versioned_manifest_json import LIMIT, bounded_json


class VersionedManifestStagingRepository:
    """Only the fixed operator-local staging draft is read or written."""

    def __init__(self, root: Path) -> None:
        self._root = root

    @staticmethod
    def _token(raw: bytes | None) -> CasToken:
        return ABSENT_TOKEN if raw is None else CasToken(TokenKind.PRESENT, hashlib.sha256(raw).hexdigest())

    @staticmethod
    def _decode(raw: bytes, catalog: ComponentCatalog, exposure: SwaggerMode,
                listen_address: str) -> InstallationManifest | UnadoptedV2Record:
        payload = bounded_json(raw)
        if type(payload) is not dict or type(payload.get("schema_version")) is not int:
            raise ValueError("Invalid draft.")
        if payload["schema_version"] == 1:
            return decode_manifest(raw)
        if payload["schema_version"] == 2:
            return validate_v2_wire(payload, catalog, exposure=exposure, listen_address=listen_address)
        raise ValueError("Invalid draft.")

    def read(self, catalog: ComponentCatalog, exposure: SwaggerMode, listen_address: str) -> ReadResult:
        try:
            with fs.staging(self._root, create=False) as parent:
                raw = fs.read_raw(parent)
                if raw is None:
                    return ReadResult(ReadStatus.ABSENT, token=ABSENT_TOKEN)
                record = self._decode(raw, catalog, exposure, listen_address)
                return ReadResult(ReadStatus.PRESENT, record, self._token(raw))
        except fs._MissingStaging:
            return ReadResult(ReadStatus.ABSENT, token=ABSENT_TOKEN)
        except Exception:
            return ReadResult(ReadStatus.BLOCKED)

    @staticmethod
    def _check_lock(parent: int, lock: int, identity: tuple[int, ...]) -> None:
        fs.check_lock(parent, lock, identity)

    def _cas_locked(self, parent: int, content: bytes, token: CasToken, catalog: ComponentCatalog,
                    exposure: SwaggerMode, listen_address: str, attempt: fs.ReplaceAttempt) -> WriteResult:
        with fs.locked(parent, self._check_lock) as (lock, identity):
            current = fs.read_raw(parent)
            if current is not None:
                self._decode(current, catalog, exposure, listen_address)
            if self._token(current) != token:
                return WriteResult(WriteStatus.CONFLICT)
            if current is not None and current == content:
                self._check_lock(parent, lock, identity)
                fs.sync_unchanged(parent, current)
                self._check_lock(parent, lock, identity)
                return WriteResult(WriteStatus.SUCCESS, self._token(content))
            fs.write_changed(parent, content, current, lock, identity, self._check_lock, attempt)
            return WriteResult(WriteStatus.SUCCESS, self._token(content))

    def compare_and_swap(self, record: UnadoptedV2Record, expected: CasToken, catalog: ComponentCatalog,
                         exposure: SwaggerMode, listen_address: str) -> WriteResult:
        attempt = fs.ReplaceAttempt()
        try:
            if type(expected) is not CasToken or type(record) is not UnadoptedV2Record:
                return WriteResult(WriteStatus.BLOCKED)
            token = CasToken(expected.kind, expected.digest)
            checked = validate_v2_wire(record.wire(), catalog, exposure=exposure, listen_address=listen_address)
            content = encode_v2_record(checked)
            if len(content) > LIMIT:
                return WriteResult(WriteStatus.BLOCKED)
            with fs.staging(self._root, create=True) as parent:
                return self._cas_locked(parent, content, token, catalog, exposure, listen_address, attempt)
        except Exception:
            return WriteResult(WriteStatus.UNCERTAIN if attempt.started else WriteStatus.BLOCKED)
