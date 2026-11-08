"""External host asset bindings supplied by repository compatibility composition.

Bindings are outside core ownership. Edition entry points may supply a different
binding file through TSW_HOST_BINDINGS_PATH. Core never assumes an edition root.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HostBinding:
    script: Path
    config: Path
    identity_assets: tuple[Path, ...]


def windows_bridge_binding(root: Path) -> HostBinding:
    manifest = Path(os.environ.get("TSW_HOST_BINDINGS_PATH", str(root / "host-bindings.json")))
    if manifest.is_symlink() or any(parent.is_symlink() for parent in manifest.parents):
        raise RuntimeError("Host integration binding must not contain symlinks.")
    try:
        values = json.loads(manifest.read_text(encoding="utf-8"))["windows_bridge"]
        if (not isinstance(values, dict)
                or any(not isinstance(values.get(key), str) or not values[key].strip()
                       for key in ("script", "config", "identity_glob"))):
            raise ValueError("Invalid host binding fields.")
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Host integration binding is malformed.") from error
    # Resolve relative paths from the binding's deployment anchor. The caller's
    # existing no-symlink/file validation also covers the manifest and inputs.
    anchor = manifest.parent
    script = Path(os.environ.get("TSW_WINDOWS_BRIDGE_SCRIPT_PATH", str(anchor / values["script"])))
    config = Path(os.environ.get("TSW_WINDOWS_BRIDGE_CONFIG_PATH", str(anchor / values["config"])))
    assets = tuple(sorted(anchor.glob(values["identity_glob"])))
    if not assets:
        raise RuntimeError("Host integration source assets are unavailable.")
    return HostBinding(script, config, tuple(dict.fromkeys((manifest, *assets, script, config))))
