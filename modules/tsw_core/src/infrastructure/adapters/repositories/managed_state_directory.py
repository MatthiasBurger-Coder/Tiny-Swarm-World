"""Create an owned private state root without repairing existing authority."""
import os
from pathlib import Path
import stat
from io import TextIOWrapper

from tiny_swarm_world.infrastructure.project_paths import default_project_paths


def _directory(path: Path, *, create_from: int, private_leaf: bool) -> int:
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for index, part in enumerate(path.parts[1:], start=1):
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            except FileNotFoundError:
                if index < create_from:
                    raise
                os.mkdir(part, 0o700, dir_fd=descriptor)
                os.fsync(descriptor)
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            info = os.fstat(descriptor)
            private = part == '.tiny-swarm-world' or (private_leaf and index == len(path.parts) - 1)
            if private:
                if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
                    raise OSError('Existing managed state authority is unsafe; preserve it for explicit review.')
            elif (info.st_uid not in {0, os.geteuid()}
                    or info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)):
                raise OSError('State directory ancestor is unsafe.')
        result, descriptor = descriptor, -1
        return result
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def managed_state_root_for_repository(root: Path | None) -> Path:
    repository = root.expanduser().resolve() if root is not None else default_project_paths().repository_root
    return repository / '.tiny-swarm-world'


def prepare_managed_state_root(path: Path) -> None:
    """Mutating writers call this; read-only path resolution never creates state."""
    absolute = Path(os.path.abspath(path))
    if '.tiny-swarm-world' not in absolute.parts:
        return
    index = absolute.parts.index('.tiny-swarm-world')
    root = Path(*absolute.parts[:index + 1])
    os.close(_directory(root, create_from=index, private_leaf=True))


def prepare_owned_log_directory(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    prepare_managed_state_root(absolute)
    descriptor = _directory(absolute, create_from=1, private_leaf=False)
    try:
        if os.fstat(descriptor).st_uid != os.geteuid():
            raise OSError('Existing log directory has a different owner.')
    finally:
        os.close(descriptor)


def open_owned_log_stream(path: Path, encoding: str | None) -> TextIOWrapper:
    absolute = Path(os.path.abspath(path))
    parent = _directory(absolute.parent, create_from=len(absolute.parts), private_leaf=False)
    descriptor = -1
    try:
        descriptor = os.open(absolute.name, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_nlink != 1 or info.st_mode & 0o022):
            raise OSError('Existing log file is unsafe; no write was performed.')
        stream = os.fdopen(descriptor, 'a', encoding=encoding)
        descriptor = -1
        return stream
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent)
