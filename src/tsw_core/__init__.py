"""Core ownership and discovery for the existing Tiny Swarm World runtime.

The distribution and tiny_swarm_world namespace remain public contracts. Module
ownership is isolated in place so preparation's no-symlink guards remain valid.
"""
from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path


def module_descriptor() -> dict:
    """Read the descriptor included in the core distribution."""
    return json.loads(files(__package__).joinpath("module.json").read_text(encoding="utf-8"))


def discover_root() -> Path:
    """Locate core assets without probing either platform edition."""
    descriptor = module_descriptor()
    for candidate in Path(__file__).resolve().parents:
        if all((candidate / descriptor[key]).is_dir() for key in ("source_root", "config_root")):
            return candidate
    raise RuntimeError("Could not locate the Tiny Swarm World core assets.")


def resource_root(root: Path, name: str) -> Path:
    """Resolve a declared core resource root relative to its deployment anchor."""
    if name not in {"source_root", "infra_root", "config_root"}:
        raise ValueError(f"Unknown core resource root: {name}")
    return root / module_descriptor()[name]
