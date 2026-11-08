"""Project selected service ports into the existing guarded WSL bridge protocol."""
from pathlib import Path
import tempfile

import yaml

from tiny_swarm_world.application.ports.host import PortWindowsCommandRunner, WindowsCommandResult


class SelectedPortRegistryRunner(PortWindowsCommandRunner):
    def __init__(self, delegate: PortWindowsCommandRunner, selected_port_ids: tuple[str, ...]):
        self.delegate = delegate
        self.selected_port_ids = selected_port_ids

    def run(self, action: str, *, script_path: Path, config_path: Path, port_registry_path: Path,
            timeout_seconds: float, distro: str | None = None, observed_address: str | None = None) -> WindowsCommandResult:
        payload = yaml.safe_load(port_registry_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("ports"), list):
            raise ValueError("Selected bridge registry is invalid")
        if any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in payload["ports"]):
            raise ValueError("Selected bridge registry has invalid port entries")
        payload["ports"] = [item for item in payload["ports"] if item["id"] in self.selected_port_ids]
        with tempfile.TemporaryDirectory(prefix="tsw-selected-ports-") as directory:
            registry = Path(directory) / "ports.yaml"
            registry.write_text(yaml.dump(payload, Dumper=_IndentedSafeDumper, sort_keys=False), encoding="utf-8")
            return self.delegate.run(action, script_path=script_path, config_path=config_path,
                                     port_registry_path=registry, timeout_seconds=timeout_seconds,
                                     distro=distro, observed_address=observed_address)


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        # The established bridge reader stops the ports block at column zero.
        return super().increase_indent(flow, False)
