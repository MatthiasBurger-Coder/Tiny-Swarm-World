"""Embed owner checks in the root-owned script, never execute writable sources."""
from __future__ import annotations

import inspect
from dataclasses import asdict

from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall import Bridge, parse_rules, verify_no_foreign_denies, exact_present, equivalent, forwarding_rules, input_rules, verify_ufw_traversal
from tiny_swarm_world.infrastructure.adapters.network_preparation.firewall_inventory import managed_nat, verify_chain, verify_nft, verify_compatibility
from tiny_swarm_world.infrastructure.adapters.network_preparation.nat_policy import bypass, bridge_set, verify_filter
from tiny_swarm_world.infrastructure.adapters.network_preparation.nat_conflicts import verify, verify_masquerade, verify_dnat


def render_guard(bridges: tuple[Bridge, ...], ufw: bool, *, absent: bool = False, ports: tuple[int, ...] = ()) -> str:
    prefix = """from __future__ import annotations
import json, shlex, subprocess, pathlib
from ipaddress import ip_network, ip_address
from types import SimpleNamespace
class NetworkPreparationFailure(RuntimeError): pass
def command(args):
    result = subprocess.run(args, check=True, capture_output=True, text=True, timeout=5)
    if result.stderr: raise RuntimeError('Incomplete firewall conversion inventory')
    return result.stdout
"""
    functions = "\n".join(inspect.getsource(function) for function in (parse_rules, verify_ufw_traversal, verify_no_foreign_denies, equivalent, exact_present, forwarding_rules, input_rules, managed_nat, verify_chain, bypass, bridge_set, verify_filter, verify_nft, verify_compatibility, verify_masquerade, verify_dnat, verify))
    tail = f"""
bridges = [SimpleNamespace(**item) for item in {tuple(asdict(bridge) for bridge in bridges)!r}]
if 'nf_tables' not in command(['iptables', '--version']): raise RuntimeError('Firewall backend changed')
owners = command(['systemctl','show','firewalld.service','nftables.service','--property=ActiveState','--property=UnitFileState'])
if 'ActiveState=active' in owners or 'UnitFileState=enabled' in owners: raise RuntimeError('Firewall owner changed')
if {absent!r}:
    if pathlib.Path('/usr/sbin/ufw').exists() or pathlib.Path('/etc/ufw').exists() or pathlib.Path('/lib/ufw').exists(): raise RuntimeError('UFW owner changed')
    status = 'Status: absent'
else:
    status = command(['ufw','status','verbose'])
if not status.startswith({'Status: absent' if absent else 'Status: active' if ufw else 'Status: inactive'!r}): raise RuntimeError('UFW owner changed')
saved = command(['iptables-save'])
rules = parse_rules(saved)
verify(saved, bridges, {ports!r})
verify_no_foreign_denies(rules, ufw={ufw!r})
if not {ufw!r}:
    for bridge in bridges:
        for chain, candidates in [('FORWARD', forwarding_rules(bridge)), ('INPUT', input_rules(bridge) if ':INPUT ACCEPT ' not in saved else ())]:
            for rule in candidates: exact_present(rule, rules.get(chain, []))
nft = json.loads(command(['nft','-j','list','ruleset']))
verify_nft(nft, bridges)
verify_compatibility(nft, saved)
routes = json.loads(command(['ip','-j','-4','route','show','default']))
if len(routes) != 1 or any(routes[0].get('dev') != bridge.egress for bridge in bridges): raise RuntimeError('Egress changed')
for bridge in bridges:
    links = json.loads(command(['ip','-j','address','show','dev',bridge.name]))
    if len(links) != 1: raise RuntimeError('Bridge identity changed')
    ipv4 = [item for item in links[0].get('addr_info',[]) if item.get('family') == 'inet']
    ipv6 = [item for item in links[0].get('addr_info',[]) if item.get('family') == 'inet6' and item.get('scope') != 'link']
    if len(ipv4) != 1 or ipv6: raise RuntimeError('Bridge address policy changed')
    address = ipv4[0]
    if address.get('local') != bridge.gateway or address.get('prefixlen') != ip_network(bridge.subnet).prefixlen: raise RuntimeError('Bridge address changed')
if ':OUTPUT ACCEPT ' not in saved and 'allow (outgoing)' not in status: raise RuntimeError('OUTPUT owner changed')
"""
    return "timeout 35 /usr/bin/python3 -I -B - <<'TSW_GUARD'\n" + prefix + functions + tail + "TSW_GUARD"
