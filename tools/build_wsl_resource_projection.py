"""Generate the resource-only Windows projection on Linux/WSL."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from ruamel.yaml import YAML

from tiny_swarm_world.domain import host_environment
from tiny_swarm_world.domain.preflight import resources as resource_module
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight.resources import default_resource_profiles

SOURCES = (
    "src/tiny_swarm_world/domain/preflight/resources.py",
    "src/tiny_swarm_world/domain/host_environment.py",
    "infra/config/node-providers/provider_config.yaml",
)
OUTPUT = "tools/windows/preparation/resource-projection.json"


def _amount(value: object) -> int:
    match = re.fullmatch(r"([1-9][0-9]*)GiB", str(value))
    if match is None:
        raise ValueError("Node resources require positive integral GiB amounts.")
    return int(match[1])


def build(root: Path) -> dict[str, object]:
    for imported, relative in ((resource_module, SOURCES[0]), (host_environment, SOURCES[1])):
        # Bind floors to exact canonical bytes; a copied equal checkout is safe.
        if Path(imported.__file__).read_bytes() != (root / relative).read_bytes():
            raise ValueError("Selected resource sources differ from imported canonical modules.")
    configuration = YAML(typ="safe").load((root / SOURCES[2]).read_text())
    nodes = configuration["nodes"]
    if not nodes or len({node["name"] for node in nodes}) != len(nodes):
        raise ValueError("Expected unique configured nodes.")
    budget = {"memory_gib": 0, "processors": 0, "disk_gib": 0}
    for node in nodes:
        resources = node["resources"]
        cpu = str(resources["cpu"])
        if re.fullmatch(r"[1-9][0-9]*", cpu) is None:
            raise ValueError("CPU limits must be positive integral counts.")
        budget["processors"] += int(cpu)
        budget["memory_gib"] += _amount(resources["memory"])
        budget["disk_gib"] += _amount(resources["disk"])
    return {
        "schema_version": 1,
        "sources": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in SOURCES},
        "node_budget": budget,
        "profiles": {
            name: {
                "memory_gib": profile.minimum.memory_bytes // 1024**3,
                "processors": profile.minimum.cpu_threads,
                "disk_gib": profile.minimum.free_disk_bytes // 1024**3,
            }
            for name, profile in default_resource_profiles(HostEnvironmentKind.WSL2).items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(build(args.repository), indent=2, sort_keys=True) + "\n"
    target = args.repository / OUTPUT
    if args.check:
        if target.read_text() != expected:
            raise SystemExit("Resource projection is stale; regenerate on Linux/WSL.")
    else:
        target.write_text(expected)


if __name__ == "__main__":
    main()
