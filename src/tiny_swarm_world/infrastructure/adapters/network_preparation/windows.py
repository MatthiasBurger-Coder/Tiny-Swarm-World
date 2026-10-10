"""WSL delegation to the existing protected Windows bridge lifecycle."""
from __future__ import annotations

import asyncio
import json
import os
from ipaddress import IPv4Address
from pathlib import Path

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.application.ports.host.port_windows_command_runner import PortWindowsCommandRunner


class WindowsNetworkPreparation:
    def __init__(self, runner: PortWindowsCommandRunner, root: Path, config_root: Path) -> None:
        self.runner, self.root, self.config_root = runner, root, config_root

    async def inspect(self, links):
        distro = os.environ.get("WSL_DISTRO_NAME", "")
        candidates = [item["local"] for link in links if link.get("ifname") == "eth0"
                      for item in link.get("addr_info", ()) if item.get("family") == "inet"]
        if not distro or len(candidates) != 1:
            raise NetworkPreparationFailure("Selected running WSL distro/IPv4 address is ambiguous.")
        address = IPv4Address(candidates[0])
        if address.is_loopback or address.is_unspecified or address.is_multicast:
            raise NetworkPreparationFailure("WSL address cannot support the existing bridge.")
        result = await self._run("inventory", distro, str(address), 30)
        try:
            state = json.loads(result.stdout)
        except ValueError:
            raise NetworkPreparationFailure("Windows bridge returned incomplete inventory.") from None
        if (not isinstance(state, dict) or state.get("schema_version") != 1
                or state.get("distro") != distro or state.get("observed_address") != str(address)
                or state.get("action") not in {None, "install", "refresh"}
                or not isinstance(state.get("blockers"), list) or not all(isinstance(item, str) for item in state["blockers"])
                or not all(isinstance(state.get(key), bool) for key in ("bridge_ready", "routing_ready", "agent_ready"))
                or not isinstance(state.get("fingerprint"), str) or not state["fingerprint"]
                or state.get("endpoint_state") != "UNVERIFIED" or state.get("login_state") != "UNVERIFIED"):
            raise NetworkPreparationFailure("Windows bridge inventory does not match the selected target.")
        return state

    async def apply(self, state):
        await self._run(state["action"], state["distro"], state["observed_address"], 180)

    async def _run(self, action, distro, address, timeout):
        result = await asyncio.to_thread(self.runner.run, action,
             script_path=self.root / "tools/windows/tws-wsl-bridge.ps1",
             config_path=self.root / "tools/windows/tws-wsl-bridge.config.json",
             port_registry_path=self.config_root / "ports.yaml", timeout_seconds=timeout,
             distro=distro, observed_address=address)
        if result.timed_out:
            raise NetworkPreparationFailure("Windows bridge deadline exceeded; inspect fresh inventory.", exit_code=124)
        if result.interrupted:
            raise NetworkPreparationFailure("Windows bridge interrupted; inspect fresh inventory.", exit_code=130)
        if result.return_code != 0:
            raise NetworkPreparationFailure("Windows bridge stopped; credentials/ownership remain with the existing lifecycle.")
        return result
