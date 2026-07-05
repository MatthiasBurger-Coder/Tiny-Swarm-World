from __future__ import annotations

import asyncio
import re
import subprocess
from collections.abc import Callable

from tiny_swarm_world.application.ports.network import (
    CommandObservation,
    ForwardingObservation,
    IncusObservation,
    LxcNodeObservation,
    RuntimeObservation,
    ServicePortObservation,
    WslHostObservation,
)


CommandExecutor = Callable[[str, int], CommandObservation]


class SubprocessNetworkProbe:
    def __init__(self, executor: CommandExecutor | None = None) -> None:
        self.executor = executor or _run_shell_command

    async def runtime(self) -> RuntimeObservation:
        version = await self._run("grep -Eqi '(microsoft|wsl)' /proc/version", timeout_seconds=3)
        hostname = await self._run("hostname -I 2>/dev/null || true", timeout_seconds=3)
        if version.ok:
            networking_mode = await self._run("wslinfo --networking-mode 2>/dev/null || true", timeout_seconds=3)
            eth0 = await self._run("ip -4 -o addr show dev eth0 scope global 2>/dev/null || true", timeout_seconds=3)
            mode = _networking_mode(networking_mode.stdout)
            return RuntimeObservation(
                runtime="wsl2",
                networking_mode=mode,
                wsl_ipv4=_first_ipv4(eth0.stdout) or _first_ipv4(hostname.stdout),
                host_ipv4="",
                commands=(version, networking_mode, hostname, eth0),
            )
        route = await self._run("ip route 2>/dev/null || true", timeout_seconds=3)
        return RuntimeObservation(
            runtime="native-linux",
            networking_mode="not-applicable",
            wsl_ipv4="",
            host_ipv4=_first_ipv4(hostname.stdout),
            commands=(version, hostname, route),
        )

    async def wsl_host(self) -> WslHostObservation:
        ip_addr, ip_route, resolv_conf, ping_egress, dns_lookup, http_probe = await asyncio.gather(
            self._run("ip addr", timeout_seconds=5),
            self._run("ip route", timeout_seconds=5),
            self._run("cat /etc/resolv.conf", timeout_seconds=5),
            self._run("ping -c1 -W2 1.1.1.1", timeout_seconds=5),
            self._run("getent hosts archive.ubuntu.com", timeout_seconds=5),
            self._run("curl -4 -I --connect-timeout 5 http://archive.ubuntu.com", timeout_seconds=8),
        )
        return WslHostObservation(
            ip_addr=ip_addr,
            ip_route=ip_route,
            resolv_conf=resolv_conf,
            ping_egress=ping_egress,
            dns_lookup=dns_lookup,
            http_probe=http_probe,
        )

    async def incus(self) -> IncusObservation:
        version = await self._run("incus version", timeout_seconds=8)
        if not version.ok:
            empty = _skipped("Incus command skipped because incus version failed.")
            return IncusObservation(
                version=version,
                network_list=empty,
                network_show=empty,
                network_info=empty,
                bridge_addr=empty,
                journal=empty,
                dnsmasq_log=empty,
            )

        network_list, network_show, network_info, bridge_addr, journal, dnsmasq_log = await asyncio.gather(
            self._run("incus network list", timeout_seconds=10),
            self._run("incus network show incusbr0", timeout_seconds=10),
            self._run("incus network info incusbr0", timeout_seconds=10),
            self._run("ip addr show incusbr0", timeout_seconds=5),
            self._run("journalctl -u incus -n 100 --no-pager", timeout_seconds=12),
            self._run("cat /var/log/incus/dnsmasq.incusbr0.log 2>/dev/null || true", timeout_seconds=5),
        )
        return IncusObservation(
            version=version,
            network_list=network_list,
            network_show=network_show,
            network_info=network_info,
            bridge_addr=bridge_addr,
            journal=journal,
            dnsmasq_log=dnsmasq_log,
            gateway_ipv4=_incus_gateway(network_show.stdout, bridge_addr.stdout),
        )

    async def lxc_node(self, node_name: str, gateway_ipv4: str) -> LxcNodeObservation:
        ping_gateway_command = (
            f"incus exec {node_name} -- ping -c1 -W2 {gateway_ipv4}"
            if gateway_ipv4
            else "printf 'incusbr0 gateway unknown' >&2; exit 1"
        )
        incus_list, ip_addr, ip_route, resolv_conf, ping_gateway, ping_egress, dns_lookup, http_probe = await asyncio.gather(
            self._run("incus list", timeout_seconds=10),
            self._run(f"incus exec {node_name} -- ip addr", timeout_seconds=10),
            self._run(f"incus exec {node_name} -- ip route", timeout_seconds=10),
            self._run(f"incus exec {node_name} -- cat /etc/resolv.conf", timeout_seconds=10),
            self._run(ping_gateway_command, timeout_seconds=8),
            self._run(f"incus exec {node_name} -- ping -c1 -W2 1.1.1.1", timeout_seconds=8),
            self._run(f"incus exec {node_name} -- getent hosts archive.ubuntu.com", timeout_seconds=8),
            self._run(
                f"incus exec {node_name} -- curl -4 -I --connect-timeout 8 http://archive.ubuntu.com",
                timeout_seconds=12,
            ),
        )
        return LxcNodeObservation(
            node_name=node_name,
            incus_list=incus_list,
            ip_addr=ip_addr,
            ip_route=ip_route,
            resolv_conf=resolv_conf,
            ping_gateway=ping_gateway,
            ping_egress=ping_egress,
            dns_lookup=dns_lookup,
            http_probe=http_probe,
        )

    async def forwarding(self) -> ForwardingObservation:
        ip_forward, iptables_forward, iptables_nat, nft_rules = await asyncio.gather(
            self._run("sysctl net.ipv4.ip_forward", timeout_seconds=5),
            self._run("iptables -S FORWARD 2>/dev/null || true", timeout_seconds=8),
            self._run("iptables -t nat -S 2>/dev/null || true", timeout_seconds=8),
            self._run(
                "nft list ruleset 2>/dev/null | "
                "grep -Ei 'incus|docker|masquerade|forward' -C 3 || true",
                timeout_seconds=10,
            ),
        )
        return ForwardingObservation(
            ip_forward=ip_forward,
            iptables_forward=iptables_forward,
            iptables_nat=iptables_nat,
            nft_rules=nft_rules,
        )

    async def service_ports(self) -> ServicePortObservation:
        return ServicePortObservation(
            listeners=await self._run("ss -ltnH 2>/dev/null || true", timeout_seconds=5)
        )

    async def _run(self, command: str, *, timeout_seconds: int) -> CommandObservation:
        return await asyncio.to_thread(self.executor, command, timeout_seconds)


def _run_shell_command(command: str, timeout: int) -> CommandObservation:
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _decoded_timeout_output(exc.stdout)
        stderr = _decoded_timeout_output(exc.stderr)
        return CommandObservation(
            command=command,
            return_code=124,
            stdout=stdout,
            stderr=stderr or f"Command timed out after {timeout} seconds.",
            timed_out=True,
        )
    except OSError as exc:
        return CommandObservation(command=command, return_code=127, stderr=str(exc))
    return CommandObservation(
        command=command,
        return_code=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def _decoded_timeout_output(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return value.strip()


def _skipped(reason: str) -> CommandObservation:
    return CommandObservation(command="skipped", return_code=1, stderr=reason)


def _networking_mode(output: str) -> str:
    normalized = output.strip().casefold()
    if normalized in {"nat", "mirrored"}:
        return normalized
    if "nat" in normalized:
        return "nat"
    if "mirrored" in normalized:
        return "mirrored"
    return "unknown"


def _first_ipv4(output: str) -> str:
    match = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b", output)
    return match.group(1) if match else ""


def _incus_gateway(network_show: str, bridge_addr: str) -> str:
    for value in (network_show, bridge_addr):
        match = re.search(r"\b(?:ipv4\.address:\s*)?(\d{1,3}(?:\.\d{1,3}){3})/\d{1,2}\b", value)
        if match:
            return match.group(1)
    return ""
