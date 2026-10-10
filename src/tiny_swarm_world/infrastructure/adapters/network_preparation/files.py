"""Read-only file planning and bounded privilege delegation for W06."""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import json
import hashlib
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.network_preparation import privileged_files
from tiny_swarm_world.infrastructure.process.async_runner import run_async_process


@dataclass(frozen=True)
class FileObservation:
    exists: bool
    content: bytes
    fingerprint: str
    mode: int
    uid: int
    gid: int


def observe(path: Path) -> FileObservation:
    return FileObservation(**privileged_files.snapshot(path))


def desired_hosts(content: bytes, names: tuple[str, ...]) -> bytes:
    return privileged_files.hosts_payload(content, names)


def helper_source_digest() -> str:
    return hashlib.sha256(Path(privileged_files.__file__).read_bytes()).hexdigest()


async def install(path: Path, before: FileObservation, payload: bytes,
                  mode: int, shared: bool = False, *, source_digest: str) -> None:
    """Invoke trusted source with isolated Python; never import the elevated cwd."""
    observation = asdict(before)
    observation["content"] = base64.b64encode(before.content).decode("ascii")
    request = json.dumps({"path": str(path), "before": observation,
                          "payload": base64.b64encode(payload).decode("ascii"),
                          "mode": mode, "shared": shared}).encode()
    source_bytes = Path(privileged_files.__file__).read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != source_digest:
        raise RuntimeError("Privileged helper source changed; a fresh plan is required")
    source = source_bytes.decode("utf-8")
    result = await run_async_process(
        ("/usr/bin/sudo", "-n", "--", "/usr/bin/python3", "-I", "-B", "-c", source),
        timeout=15, input_data=request,
    )
    if result.timed_out:
        raise TimeoutError("Protected-file transaction timed out; a fresh plan is required")
    if result.returncode != 0:
        raise RuntimeError("Protected-file transaction failed; a fresh plan is required")
