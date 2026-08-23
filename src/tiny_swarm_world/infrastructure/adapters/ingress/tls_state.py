from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path


def canonical_tls_state_root(environment: Mapping[str, str] | None = None) -> Path:
    values = os.environ if environment is None else environment
    explicit = values.get("TSW_LOCAL_TLS_STATE_ROOT", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()
    xdg_state = values.get("XDG_STATE_HOME", "").strip()
    base = Path(xdg_state).expanduser() if xdg_state else Path.home() / ".local" / "state"
    return (base / "tiny-swarm-world" / "tls" / "traefik").resolve()
