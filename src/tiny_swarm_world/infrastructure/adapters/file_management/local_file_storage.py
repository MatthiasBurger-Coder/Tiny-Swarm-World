from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from tiny_swarm_world.application.ports.file_management.port_local_file_storage import (
    PortLocalFileStorage,
    TextFileSnapshot,
)


class LocalFileStorage(PortLocalFileStorage):
    """POSIX-oriented storage adapter for installer configuration and evidence."""

    def load_yaml(self, path: Path) -> object:
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def read_text(self, path: Path) -> str | None:
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def scan_text_files(
        self,
        root: Path,
        *,
        suffixes: frozenset[str],
        skip_parts: frozenset[str],
    ) -> tuple[TextFileSnapshot, ...]:
        if any(part in skip_parts for part in root.parts):
            return ()
        candidate_paths: list[Path] = []
        for current_root, directory_names, file_names in os.walk(root, topdown=True):
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

    def write_text(self, path: Path, text: str, *, private: bool = False) -> None:
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
            temporary_path.unlink(missing_ok=True)
            raise

    def ensure_directory(self, path: Path, *, private: bool = False) -> None:
        path.mkdir(parents=True, exist_ok=True)
        if private:
            path.chmod(0o700)

    def exists(self, path: Path) -> bool:
        return path.exists()
