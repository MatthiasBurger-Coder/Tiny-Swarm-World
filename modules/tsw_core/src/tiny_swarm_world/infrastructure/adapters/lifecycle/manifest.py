"""Private, atomic installation-instance persistence with optimistic concurrency."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile

from pydantic import ValidationError

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestSnapshot
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest


def decode_manifest(content: bytes) -> InstallationManifest:
    """Identity migration for v1; no legacy/future migration is admitted yet."""
    try:
        payload = json.loads(content, object_pairs_hook=_unique_object)
        if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int:
            raise ValueError("Missing schema")
        if payload["schema_version"] != 1:
            raise LifecycleStateError(
                "Unsupported installation schema; use matching TSW code or a reviewed explicit migration."
            )
        if type(payload.get("catalog_version")) is not int:
            raise ValueError("Invalid catalog version")
        return InstallationManifest.model_validate_json(content)
    except (ValueError, UnicodeError, ValidationError) as error:
        if isinstance(error, LifecycleStateError):
            raise
        raise LifecycleStateError(
            "Invalid installation manifest; preserve the file and restore a verified backup or inspect legacy state."
        ) from None


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


class JsonManifestRepository:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> ManifestSnapshot:
        try:
            if self.path.is_symlink():
                raise LifecycleStateError("Manifest must be a regular local file; inspect the symlink manually.")
            interrupted = tuple(self.path.parent.glob(".installation-manifest-*.tmp"))
            notes = ("interrupted_write: inspect retained temporary files; only the final manifest is authoritative",) if interrupted else ()
            if not self.path.exists():
                return ManifestSnapshot(None, None, notes + ("adoption_required: no manifest; inspect legacy inventory explicitly",))
            content = self.path.read_bytes()
            return ManifestSnapshot(decode_manifest(content), hashlib.sha256(content).hexdigest(), notes)
        except OSError:
            raise LifecycleStateError("Cannot read installation state; check local file access without resetting it.") from None

    def save(self, manifest: InstallationManifest, *, expected_token: str | None) -> ManifestSnapshot:
        # Revalidate even instances whose nested mutable mappings were changed.
        content = manifest.model_dump_json(indent=2).encode() + b"\n"
        decode_manifest(content)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            lock_path = self.path.with_suffix(".lock")
            descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                current = self.load()
                if current.token != expected_token:
                    raise LifecycleStateError("Installation state changed; inspect again before retrying the write.")
                if current.manifest == manifest:
                    return current
                self._replace(content)
                return self.load()
        except OSError:
            raise LifecycleStateError(
                "Manifest write interrupted or durability uncertain; inspect final state before retrying."
            ) from None

    def _replace(self, content: bytes) -> None:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".installation-manifest-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
