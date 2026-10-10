"""Exact approved source/configuration identity; operator trust remains explicit."""
from pathlib import Path
import hashlib

def preparation_asset_hashes(repository_root: Path, *, is_wsl: bool) -> tuple[str, ...]:
    assets = ("requirements.lock", "requirements.build.lock", "pyproject.toml",
              "infra/config/host/tiny-swarm-world-sysctl.conf",
              "infra/config/host/tiny-swarm-world-modules.conf",
              "infra/config/node-providers/provider_config.yaml", "infra/config/ports.yaml")
    required = ("prepare_network.py", "domain/network_preparation.py", "application/ports/network_preparation.py",
                "application/services/network_preparation.py", "infrastructure/composition_network_preparation.py",
                "infrastructure/adapters/network_preparation/files.py", "infrastructure/adapters/network_preparation/privileged_files.py")
    if any(not (repository_root / "src/tiny_swarm_world" / name).is_file() for name in required):
        raise RuntimeError("Complete W06 runtime assets required.")
    if any(path.is_symlink() for path in (repository_root / "src").rglob("*")):
        raise RuntimeError("Preparation runtime directory links are unsafe.")
    runtime = tuple(sorted((repository_root / "src/tiny_swarm_world").rglob("*.py")))
    inputs = tuple(repository_root / name for name in assets) + runtime
    if is_wsl:
        inputs += tuple(sorted((repository_root / "tools/windows").rglob("*.ps1")))
        inputs += (repository_root / "tools/windows/tws-wsl-bridge.config.json",)
    if any(path.is_symlink() or not path.is_file() or any(parent.is_symlink() for parent in path.parents)
           for path in inputs):
        raise RuntimeError("Preparation source/configuration asset is unsafe or unavailable.")
    return tuple(str(path.relative_to(repository_root)) + ":" + hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs)
