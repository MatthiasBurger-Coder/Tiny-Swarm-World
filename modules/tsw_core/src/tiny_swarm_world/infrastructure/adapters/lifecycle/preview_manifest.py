"""Preview-only manifest port backed by bounded descriptor reads."""
from __future__ import annotations

import hashlib

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestSnapshot
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import decode_manifest
from tiny_swarm_world.infrastructure.adapters.lifecycle.preview_file_reader import MANIFEST, PreviewFileReader


class PreviewManifestRepository:
    def __init__(self, reader: PreviewFileReader) -> None:
        self._reader = reader

    def load(self) -> ManifestSnapshot:
        content = self._reader.read(MANIFEST)
        return ManifestSnapshot(decode_manifest(content), hashlib.sha256(content).hexdigest())

    def save(self, manifest: InstallationManifest, *, expected_token: str | None) -> ManifestSnapshot:
        raise LifecycleStateError("Preview is read-only.")
