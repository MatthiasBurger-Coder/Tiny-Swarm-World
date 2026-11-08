"""Exact approved source/configuration identity; operator trust remains explicit."""
from pathlib import Path
import hashlib

def preparation_asset_hashes(repository_root: Path, *, is_wsl: bool) -> tuple[str, ...]:
    assets = ("requirements.lock", "requirements.build.lock", "pyproject.toml",
              "modules/tsw_core/infra/config/host/tiny-swarm-world-sysctl.conf",
              "modules/tsw_core/infra/config/host/tiny-swarm-world-modules.conf",
              "modules/tsw_core/infra/config/node-providers/provider_config.yaml", "modules/tsw_core/infra/config/ports.yaml")
    required = ("prepare_network.py", "domain/network_preparation.py", "application/ports/network_preparation.py",
                "application/services/network_preparation.py", "infrastructure/composition_network_preparation.py",
                "infrastructure/adapters/network_preparation/files.py", "infrastructure/adapters/network_preparation/privileged_files.py")
    if any(not (repository_root / "modules/tsw_core/src" / name).is_file() for name in required):
        raise RuntimeError("Complete W06 runtime assets required.")
    if any(path.is_symlink() for path in (repository_root / "modules/tsw_core/src").rglob("*")):
        raise RuntimeError("Preparation runtime directory links are unsafe.")
    runtime = tuple(sorted((repository_root / "modules/tsw_core/src").rglob("*.py")))
    descriptor = repository_root / "modules/tsw_core/src/module.json"
    if descriptor.is_file():
        runtime += (repository_root / "modules/tsw_core/__init__.py", descriptor)
    compatibility = (
        "src/tiny_swarm_world/__init__.py", "src/tsw_core/__init__.py",
        "modules/tsw_native_linux/boostrap/prepare_linux.sh", "modules/tsw_native_linux/boostrap/install.sh", "modules/tsw_native_linux/boostrap/run.sh",
    )
    forwarders = tuple(repository_root / name for name in compatibility
                       if (repository_root / name).exists() or (repository_root / name).is_symlink())
    inputs = tuple(repository_root / name for name in assets) + runtime + forwarders
    if is_wsl:
        from tiny_swarm_world.infrastructure.host_bindings import windows_bridge_binding

        inputs += windows_bridge_binding(repository_root).identity_assets
    if any(path.is_symlink() or not path.is_file() or any(parent.is_symlink() for parent in path.parents)
           for path in inputs):
        raise RuntimeError("Preparation source/configuration asset is unsafe or unavailable.")
    return tuple(str(path.relative_to(repository_root)) + ":" + hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs)
