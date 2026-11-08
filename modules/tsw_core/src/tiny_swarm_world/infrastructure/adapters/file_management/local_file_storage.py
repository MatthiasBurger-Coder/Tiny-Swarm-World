from __future__ import annotations

from tiny_swarm_world.application.ports.file_management.port_local_file_storage import LocalFileStorageError, LocalFileContentError
from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure

import os
import tempfile
from pathlib import Path

from tiny_swarm_world.application.ports.file_management.port_local_file_storage import (
    PortLocalFileStorage,
    TextFileSnapshot,
)


class LocalFileStorage(PortLocalFileStorage):
    """POSIX-oriented storage adapter for installer configuration and evidence."""

    def read_text(self, path: Path) -> str | None:
        try:
            if not path.exists():
                return None
            return path.read_text(encoding="utf-8")
        except OperationError:
            raise
        except OSError:
            raise LocalFileStorageError(OperationFailure.for_cause("storage.read", "local_storage", "filesystem_error")) from None
        except UnicodeError:
            raise LocalFileContentError(OperationFailure.for_cause("storage.read", "local_storage", "configuration_invalid")) from None

    def scan_text_files(
        self,
        root: Path,
        *,
        suffixes: frozenset[str],
        skip_parts: frozenset[str],
    ) -> tuple[TextFileSnapshot, ...]:
        try:
            if any(part in skip_parts for part in root.parts):
                return ()
            candidate_paths: list[Path] = []
            for current_root, directory_names, file_names in os.walk(root, topdown=True, onerror=_raise_walk_error):
                directory_names[:] = sorted(
                    name for name in directory_names if name not in skip_parts
                )
                current_path = Path(current_root)
                for file_name in sorted(file_names):
                    path = current_path / file_name
                    if not (
                        path.name.startswith(".env")
                        or path.suffix in suffixes
                        or "docker-compose" in path.name
                    ):
                        continue
                    candidate_paths.append(path)

            snapshots: list[TextFileSnapshot] = []
            for path in sorted(candidate_paths):
                if not path.is_file():
                    continue
                snapshots.append(
                    TextFileSnapshot(
                        path=path,
                        text=path.read_text(encoding="utf-8", errors="ignore"),
                    )
                )
            return tuple(snapshots)
        except OperationError:
            raise
        except OSError:
            raise LocalFileStorageError(OperationFailure.for_cause("storage.scan", "local_storage", "filesystem_error")) from None
        except UnicodeError:
            raise LocalFileContentError(OperationFailure.for_cause("storage.scan", "local_storage", "configuration_invalid")) from None

    def write_text(self, path: Path, text: str, *, private: bool = False) -> None:
        try:
            self.ensure_directory(path.parent, private=private)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=path.parent,
                prefix=f".{path.name}.",
            )
            temporary_path = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                    stream.write(text)
                if private:
                    temporary_path.chmod(0o600)
                temporary_path.replace(path)
            except BaseException:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
        except OperationError:
            raise
        except OSError:
            raise LocalFileStorageError(OperationFailure.for_cause("storage.write", "local_storage", "filesystem_error")) from None
        except UnicodeError:
            raise LocalFileContentError(OperationFailure.for_cause("storage.write", "local_storage", "configuration_invalid")) from None

    def ensure_directory(self, path: Path, *, private: bool = False) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            if private:
                path.chmod(0o700)
        except OperationError:
            raise
        except OSError:
            raise LocalFileStorageError(OperationFailure.for_cause("storage.directory", "local_storage", "filesystem_error")) from None
        except UnicodeError:
            raise LocalFileContentError(OperationFailure.for_cause("storage.directory", "local_storage", "configuration_invalid")) from None

    def exists(self, path: Path) -> bool:
        try:
            return path.exists()
        except OperationError:
            raise
        except OSError:
            raise LocalFileStorageError(OperationFailure.for_cause("storage.exists", "local_storage", "filesystem_error")) from None
        except UnicodeError:
            raise LocalFileContentError(OperationFailure.for_cause("storage.exists", "local_storage", "configuration_invalid")) from None

    def directory_exists(self, path: Path) -> bool:
        try:
            return path.is_dir()
        except OperationError:
            raise
        except OSError:
            raise LocalFileStorageError(OperationFailure.for_cause("storage.directory", "local_storage", "filesystem_error")) from None
        except UnicodeError:
            raise LocalFileContentError(OperationFailure.for_cause("storage.directory", "local_storage", "configuration_invalid")) from None


def _raise_walk_error(error: OSError) -> None:
    raise error
