from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.application.ports.network import (
    CommandObservation,
    ForwardingObservation,
    IncusObservation,
    LxcNodeObservation,
    NetworkRepairMutationResult,
    PortNetworkProbe,
    PortNetworkRepair,
    RuntimeObservation,
    ServicePortObservation,
    WslHostObservation,
)
from tiny_swarm_world.domain.network import PortExposureClass, PortRegistry


DEFAULT_INCUS_BRIDGE = "incusbr0"
DEFAULT_MANAGER_NODE = "swarm-manager"
WSL2_NAT_RUNTIME = "wsl2-nat"


class DiagnosticSeverity(str, Enum):
    OK = "ok"
    INFO = "info"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class NetworkDiagnostic:
    code: str
    severity: DiagnosticSeverity
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
        }


@dataclass(frozen=True)
class NetworkDiagnosticSection:
    title: str
    lines: tuple[str, ...]
    diagnostics: tuple[NetworkDiagnostic, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "lines": list(self.lines),
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


@dataclass(frozen=True)
class NetworkDoctorReport:
    sections: tuple[NetworkDiagnosticSection, ...]

    @property
    def passed(self) -> bool:
        return all(
            diagnostic.severity is not DiagnosticSeverity.FAIL
            for section in self.sections
            for diagnostic in section.diagnostics
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "sections": [section.to_dict() for section in self.sections],
        }

    def render(self) -> str:
        output: list[str] = []
        for section in self.sections:
            output.append(f"[{section.title}]")
            output.extend(section.lines)
            for diagnostic in section.diagnostics:
                output.append(
                    f"{diagnostic.severity.value.upper()}: "
                    f"{diagnostic.code}: {diagnostic.message}"
                )
            output.append("")
        return "\n".join(output).rstrip()


@dataclass(frozen=True)
class NetworkRepairOptions:
    runtime: str | None = None
    linux_forwarding: bool = False
    incus: bool = False
    apply: bool = False

    @property
    def has_target(self) -> bool:
        return bool(self.runtime or self.linux_forwarding or self.incus)


@dataclass(frozen=True)
class NetworkRepairStep:
    target: str
    status: str
    message: str
    details: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "status": self.status,
            "message": self.message,
            "details": list(self.details),
        }


@dataclass(frozen=True)
class NetworkRepairReport:
    apply: bool
    steps: tuple[NetworkRepairStep, ...]

    @property
    def succeeded(self) -> bool:
        return all(step.status not in {"failed", "blocked"} for step in self.steps)

    def to_dict(self) -> dict[str, object]:
        return {
            "apply": self.apply,
            "succeeded": self.succeeded,
            "steps": [step.to_dict() for step in self.steps],
        }

    def render(self) -> str:
        lines = ["[Network Repair]", f"Mode: {'apply' if self.apply else 'dry-run'}"]
        for step in self.steps:
            lines.append(f"- {step.target}: {step.status}")
            lines.append(f"  {step.message}")
            lines.extend(f"  {detail}" for detail in step.details)
        return "\n".join(lines)


class NetworkDoctorService:
    def __init__(
        self,
        probe: PortNetworkProbe,
        port_registry: PortRegistry,
        *,
        manager_node: str = DEFAULT_MANAGER_NODE,
    ) -> None:
        self.probe = probe
        self.port_registry = port_registry
        self.manager_node = manager_node

    async def run(self) -> NetworkDoctorReport:
        runtime = await self.probe.runtime()
        sections: list[NetworkDiagnosticSection] = [_runtime_section(runtime)]

        wsl_diagnostics: tuple[NetworkDiagnostic, ...] = ()
        if runtime.is_wsl2:
            wsl_host = await self.probe.wsl_host()
            wsl_section = _wsl_host_section(wsl_host)
            wsl_diagnostics = wsl_section.diagnostics
            sections.append(wsl_section)
        else:
            sections.append(
                NetworkDiagnosticSection(
                    "Windows \u2194 WSL",
                    ("Not applicable for native-linux runtime.",),
                    (_info("WINDOWS_WSL_NOT_APPLICABLE", "Native Linux does not use Windows portproxy."),),
                )
            )

        incus = await self.probe.incus()
        incus_section = _incus_section(incus)
        sections.append(incus_section)

        lxc_section: NetworkDiagnosticSection | None = None
        if _incus_available(incus):
            lxc_node = await self.probe.lxc_node(self.manager_node, incus.gateway_ipv4)
            lxc_section = _lxc_node_section(lxc_node)
            sections.append(lxc_section)
        else:
            sections.append(
                NetworkDiagnosticSection(
                    "LXC Nodes",
                    (f"{self.manager_node}: skipped because Incus is not available.",),
                    (_warn("LXC_SKIPPED", "LXC node checks require a working Incus daemon."),),
                )
            )

        forwarding = await self.probe.forwarding()
        sections.append(_forwarding_section(forwarding, lxc_section))
        sections.append(_windows_portproxy_section(runtime))

        service_ports = await self.probe.service_ports()
        sections.append(_service_ports_section(self.port_registry, service_ports))
        sections.append(_final_diagnosis_section(tuple(sections), wsl_diagnostics, runtime))

        return NetworkDoctorReport(tuple(sections))


class NetworkRepairService:
    def __init__(
        self,
        probe: PortNetworkProbe,
        repair: PortNetworkRepair,
        *,
        bridge: str = DEFAULT_INCUS_BRIDGE,
        manager_node: str = DEFAULT_MANAGER_NODE,
    ) -> None:
        self.probe = probe
        self.repair = repair
        self.bridge = bridge
        self.manager_node = manager_node

    async def run(self, options: NetworkRepairOptions) -> NetworkRepairReport:
        if not options.has_target:
            return NetworkRepairReport(
                options.apply,
                (
                    NetworkRepairStep(
                        "network",
                        "blocked",
                        "No repair target was selected.",
                        (
                            "Use --runtime wsl2-nat, --linux-forwarding, or --incus.",
                            "Add --apply only after reviewing the dry-run output.",
                        ),
                    ),
                ),
            )

        steps: list[NetworkRepairStep] = []
        if options.runtime is not None:
            steps.append(await self._runtime_step(options.runtime, options.apply))
        if options.incus:
            steps.append(await self._incus_step(options.apply))
        if options.linux_forwarding:
            steps.append(await self._linux_forwarding_step(options.apply))
        return NetworkRepairReport(options.apply, tuple(steps))

    async def _runtime_step(self, runtime: str, apply: bool) -> NetworkRepairStep:
        observed = await self.probe.runtime()
        if runtime != WSL2_NAT_RUNTIME:
            return NetworkRepairStep(
                "runtime",
                "blocked",
                f"Unsupported repair runtime: {runtime}",
                ("Supported runtime repair target: wsl2-nat.",),
            )
        if not observed.is_wsl2:
            return NetworkRepairStep(
                "runtime",
                "skipped",
                "Runtime repair is only applicable inside WSL2.",
                (f"Observed runtime: {observed.runtime}",),
            )
        if observed.networking_mode == "nat":
            return NetworkRepairStep(
                "runtime",
                "skipped",
                "WSL is already running in NAT networking mode.",
                ("No .wslconfig change is required.",),
            )
        details = (
            "WSL is running in mirrored networking mode."
            if observed.networking_mode == "mirrored"
            else f"WSL networking mode is {observed.networking_mode}."
        )
        recommendation = (
            "Tiny-Swarm-World with Incus/LXC is validated for wsl2-nat.",
            "This changes global WSL behavior.",
            "Backup and apply only with:",
            "  ./tsw network repair --runtime wsl2-nat --apply",
        )
        if not apply:
            return NetworkRepairStep(
                "runtime",
                "planned",
                "Would set WSL networkingMode to nat in the Windows user .wslconfig.",
                (details, *recommendation),
            )
        return _mutation_step(await self.repair.apply_wsl2_nat_runtime())

    async def _incus_step(self, apply: bool) -> NetworkRepairStep:
        details = (
            "Would inspect /var/lib/incus/networks/incusbr0/dnsmasq.pid.",
            "Would remove it only if no dnsmasq process is running, "
            "the referenced PID is absent, and the file is under the Incus incusbr0 runtime path.",
            "Would restart the Incus service and recheck incusbr0.",
        )
        if not apply:
            return NetworkRepairStep(
                "incus",
                "planned",
                "Would run the guarded Incus bridge repair.",
                details,
            )
        return _mutation_step(await self.repair.apply_incus_repair())

    async def _linux_forwarding_step(self, apply: bool) -> NetworkRepairStep:
        details = (
            f"Bridge: {self.bridge}",
            "Would add idempotent FORWARD accept rules scoped to the Incus bridge.",
            "Would install tsw-incus-forwarding.service for reboot persistence.",
            f"Would verify with incus exec {self.manager_node} -- curl -4 -I "
            "--connect-timeout 8 http://archive.ubuntu.com",
        )
        if not apply:
            return NetworkRepairStep(
                "linux-forwarding",
                "planned",
                "Would apply persistent Incus forwarding rules.",
                details,
            )
        return _mutation_step(
            await self.repair.apply_linux_forwarding(self.bridge, self.manager_node)
        )


def _runtime_section(runtime: RuntimeObservation) -> NetworkDiagnosticSection:
    if runtime.is_wsl2:
        lines: tuple[str, ...] = (
            "Runtime: wsl2",
            f"Networking mode: {runtime.networking_mode}",
            f"WSL IPv4: {runtime.wsl_ipv4 or 'unknown'}",
        )
        diagnostics = (
            _ok("RUNTIME_WSL2", "WSL2 runtime detected."),
            _runtime_networking_diagnostic(runtime),
        )
        return NetworkDiagnosticSection("Runtime", lines, diagnostics)

    lines = (
        "Runtime: native-linux",
        f"Host IPv4: {runtime.host_ipv4 or 'unknown'}",
    )
    return NetworkDiagnosticSection(
        "Runtime",
        lines,
        (_ok("RUNTIME_NATIVE_LINUX", "Native Linux runtime detected."),),
    )


def _runtime_networking_diagnostic(runtime: RuntimeObservation) -> NetworkDiagnostic:
    if runtime.networking_mode == "nat":
        return _ok("WSL2_NAT", "WSL networking mode is nat.")
    if runtime.networking_mode == "mirrored":
        return _warn(
            "WSL2_MIRRORED",
            "WSL mirrored networking is not the validated Incus/LXC profile.",
        )
    return _warn("WSL2_NETWORKING_UNKNOWN", "WSL networking mode could not be determined.")


def _wsl_host_section(observation: WslHostObservation) -> NetworkDiagnosticSection:
    diagnostics: list[NetworkDiagnostic] = []
    route_ok = _has_default_route(observation.ip_route.stdout)
    dns_ok = observation.dns_lookup.ok
    ping_ok = observation.ping_egress.ok
    http_ok = observation.http_probe.ok

    if not route_ok:
        diagnostics.append(_fail("WSL_NO_DEFAULT_ROUTE", "WSL has no default route."))
    if not dns_ok:
        diagnostics.append(_fail("WSL_DNS_BROKEN", "WSL cannot resolve archive.ubuntu.com."))
    if not ping_ok:
        diagnostics.append(_fail("WSL_NO_EGRESS", "WSL cannot ping 1.1.1.1."))
    if not http_ok:
        diagnostics.append(_fail("WSL_HTTP_BLOCKED", "WSL HTTP egress to archive.ubuntu.com failed."))
    if route_ok and dns_ok and ping_ok and http_ok:
        diagnostics.append(_ok("WSL_OK", "WSL host networking is healthy."))

    return NetworkDiagnosticSection(
        "WSL Host",
        (
            f"Default route: {'OK' if route_ok else 'missing'}",
            f"DNS archive.ubuntu.com: {'OK' if dns_ok else 'failed'}",
            f"Ping 1.1.1.1: {'OK' if ping_ok else 'failed'}",
            f"HTTP archive.ubuntu.com: {'OK' if http_ok else 'failed'}",
            f"WSL egress: {'OK' if route_ok and dns_ok and ping_ok and http_ok else 'FAILED'}",
        ),
        tuple(diagnostics),
    )


def _incus_section(observation: IncusObservation) -> NetworkDiagnosticSection:
    diagnostics: list[NetworkDiagnostic] = []
    combined_version = observation.version.combined_output.casefold()
    combined_network = "\n".join(
        (
            observation.network_list.combined_output,
            observation.network_show.combined_output,
            observation.network_info.combined_output,
            observation.journal.combined_output,
            observation.dnsmasq_log.combined_output,
        )
    ).casefold()
    dnsmasq_output = observation.dnsmasq_log.combined_output.casefold()
    bridge_available = observation.network_info.ok and observation.bridge_addr.ok

    if _command_missing(observation.version):
        diagnostics.append(_fail("INCUS_NOT_INSTALLED", "The incus command is not available."))
    elif not observation.version.ok:
        diagnostics.append(_fail("INCUS_NOT_RUNNING", "Incus did not respond to incus version."))
    elif "incusbr0" not in observation.network_list.stdout and not observation.network_show.ok:
        diagnostics.append(_fail("INCUSBR0_MISSING", "Incus network incusbr0 is missing."))
    elif "unavailable" in combined_network:
        diagnostics.append(
            _fail(
                "INCUSBR0_UNAVAILABLE",
                "incusbr0 is unavailable; do not delete runtime files automatically.",
            )
        )
    elif _mentions_failure(dnsmasq_output) or (
        "dnsmasq" in combined_network and _mentions_failure(combined_network) and not bridge_available
    ):
        diagnostics.append(_fail("INCUS_DNSMASQ_FAILED", "Incus dnsmasq appears to have failed."))
    else:
        diagnostics.append(_ok("INCUSBR0_OK", "Incus network incusbr0 is available."))

    lines = [
        f"incus version: {'OK' if observation.version.ok else 'failed'}",
        f"incusbr0 gateway: {observation.gateway_ipv4 or 'unknown'}",
        "Incus network incusbr0: "
        f"{'OK' if diagnostics[-1].code == 'INCUSBR0_OK' else 'FAILED'}",
    ]
    if any(diagnostic.code == "INCUSBR0_UNAVAILABLE" for diagnostic in diagnostics):
        lines.extend(
            (
                "incusbr0 unavailable.",
                "Possible causes:",
                "- dnsmasq failed",
                "- stale runtime state",
                "- WSL mirrored networking conflict",
                "- port 53/67 conflict",
                "- bridge device missing",
            )
        )
    if "permission denied" in combined_version:
        lines.append("Incus access was denied; check group/socket access outside the installer.")
    return NetworkDiagnosticSection("Incus", tuple(lines), tuple(diagnostics))


def _lxc_node_section(observation: LxcNodeObservation) -> NetworkDiagnosticSection:
    route_ok = _has_default_route(observation.ip_route.stdout)
    gateway_ok = observation.ping_gateway.ok
    dns_ok = observation.dns_lookup.ok
    ping_ok = observation.ping_egress.ok
    http_ok = observation.http_probe.ok
    diagnostics: list[NetworkDiagnostic] = []

    if not observation.incus_list.ok or observation.node_name not in observation.incus_list.stdout:
        diagnostics.append(_fail("LXC_NODE_MISSING", f"{observation.node_name} is not listed by Incus."))
    if not gateway_ok:
        diagnostics.append(_fail("LXC_NO_GATEWAY", f"{observation.node_name} cannot reach incusbr0."))
    if not route_ok:
        diagnostics.append(_fail("LXC_NO_DEFAULT_ROUTE", f"{observation.node_name} has no default route."))
    if not dns_ok:
        diagnostics.append(_fail("LXC_DNS_BROKEN", f"{observation.node_name} cannot resolve archive.ubuntu.com."))
    if not ping_ok:
        diagnostics.append(_fail("LXC_NO_EGRESS", f"{observation.node_name} cannot ping 1.1.1.1."))
    if not http_ok:
        diagnostics.append(_fail("LXC_HTTP_BLOCKED", f"{observation.node_name} HTTP egress failed."))
    if gateway_ok and route_ok and dns_ok and ping_ok and http_ok:
        diagnostics.append(_ok("LXC_EGRESS_OK", f"{observation.node_name} egress is healthy."))

    return NetworkDiagnosticSection(
        "LXC Nodes",
        (
            f"LXC {observation.node_name} gateway: {'OK' if gateway_ok else 'FAILED'}",
            f"LXC {observation.node_name} default route: {'OK' if route_ok else 'FAILED'}",
            f"LXC {observation.node_name} DNS: {'OK' if dns_ok else 'FAILED'}",
            f"LXC {observation.node_name} HTTP egress: {'OK' if http_ok else 'FAILED'}",
        ),
        tuple(diagnostics),
    )


def _forwarding_section(
    observation: ForwardingObservation,
    lxc_section: NetworkDiagnosticSection | None,
) -> NetworkDiagnosticSection:
    ip_forward_ok = " = 1" in observation.ip_forward.stdout or observation.ip_forward.stdout.strip().endswith("= 1")
    forward_policy_drop = "-P FORWARD DROP" in observation.iptables_forward.stdout
    docker_rules_present = "DOCKER" in observation.iptables_forward.stdout
    incus_forwarding_present = _incus_forward_rules_present(observation.iptables_forward.stdout)
    masquerade_present = _incus_masquerade_present(observation.iptables_nat.stdout, observation.nft_rules.stdout)
    lxc_egress_failed = _section_has_any(
        lxc_section,
        ("LXC_NO_EGRESS", "LXC_HTTP_BLOCKED", "LXC_NO_GATEWAY"),
    )
    diagnostics: list[NetworkDiagnostic] = []

    if not ip_forward_ok:
        diagnostics.append(_fail("IP_FORWARD_DISABLED", "net.ipv4.ip_forward is not enabled."))
    if forward_policy_drop:
        diagnostics.append(_warn("FORWARD_POLICY_DROP", "iptables FORWARD policy is DROP."))
    if forward_policy_drop and docker_rules_present and not incus_forwarding_present and lxc_egress_failed:
        diagnostics.append(
            _fail(
                "INCUS_FORWARDING_BLOCKED_BY_DOCKER",
                "Docker FORWARD policy appears to block incusbr0 egress.",
            )
        )
    if not masquerade_present:
        diagnostics.append(_warn("INCUS_NAT_MISSING", "Incus NAT masquerade was not observed."))
    if not any(diagnostic.severity is DiagnosticSeverity.FAIL for diagnostic in diagnostics):
        diagnostics.append(_ok("FORWARDING_OK", "Docker/Incus forwarding is acceptable."))

    return NetworkDiagnosticSection(
        "Docker/iptables",
        (
            f"IP forwarding: {'OK' if ip_forward_ok else 'disabled'}",
            f"FORWARD policy DROP: {'yes' if forward_policy_drop else 'no'}",
            f"Docker rules present: {'yes' if docker_rules_present else 'no'}",
            f"incusbr0 forwarding rules: {'present' if incus_forwarding_present else 'not observed'}",
            f"MASQUERADE: {'present' if masquerade_present else 'not observed'}",
            "Docker/Incus forwarding: "
            f"{'OK' if not any(item.severity is DiagnosticSeverity.FAIL for item in diagnostics) else 'FAILED'}",
        ),
        tuple(diagnostics),
    )


def _windows_portproxy_section(runtime: RuntimeObservation) -> NetworkDiagnosticSection:
    if not runtime.is_wsl2:
        return NetworkDiagnosticSection(
            "Windows Portproxy",
            ("Not applicable for native-linux runtime.",),
            (_info("WINDOWS_PORTPROXY_NOT_APPLICABLE", "Native Linux does not use Windows portproxy."),),
        )
    return NetworkDiagnosticSection(
        "Windows Portproxy",
        (
            "Windows-side checks require elevated PowerShell.",
            "Run:",
            "  powershell.exe -ExecutionPolicy Bypass -File .\\tools\\windows\\doctor-portproxy.ps1",
            "Repair:",
            "  powershell.exe -ExecutionPolicy Bypass -File .\\tools\\windows\\repair-wsl-portproxy.ps1",
        ),
        (
            _warn(
                "WINDOWS_PORTPROXY_REQUIRES_WINDOWS_CHECK",
                "WSL cannot fully verify Windows portproxy and firewall state.",
            ),
        ),
    )


def _service_ports_section(
    port_registry: PortRegistry,
    observation: ServicePortObservation,
) -> NetworkDiagnosticSection:
    ports = _host_integration_ports(port_registry)
    listener_ports = _listener_ports(observation.listeners.stdout)
    listening = tuple(port for port in ports if port in listener_ports)
    missing = tuple(port for port in ports if port not in listener_ports)
    return NetworkDiagnosticSection(
        "Service Ports",
        (
            "Registry: infra/config/ports.yaml",
            "Host integration ports: " + _format_ports(ports),
            "Listening now: " + (_format_ports(listening) if listening else "none observed"),
            "Not listening now: " + (_format_ports(missing) if missing else "none"),
        ),
        (
            _ok("SERVICE_PORT_REGISTRY_LOADED", "Service ports were loaded from the central registry."),
        ),
    )


def _final_diagnosis_section(
    sections: tuple[NetworkDiagnosticSection, ...],
    wsl_diagnostics: tuple[NetworkDiagnostic, ...],
    runtime: RuntimeObservation,
) -> NetworkDiagnosticSection:
    diagnostics = tuple(
        diagnostic
        for section in sections
        for diagnostic in section.diagnostics
        if diagnostic.severity is DiagnosticSeverity.FAIL
    )
    lines: list[str] = []
    if not diagnostics:
        lines.append("Final diagnosis: OK")
        return NetworkDiagnosticSection(
            "Final Diagnosis",
            tuple(lines),
            (_ok("NETWORK_OK", "No blocking network diagnostics were found."),),
        )

    lines.append("Final diagnosis: FAILED")
    lines.append("Blocking diagnostics: " + ", ".join(diagnostic.code for diagnostic in diagnostics))
    lines.extend(_repair_hints(diagnostics, wsl_diagnostics, runtime))
    return NetworkDiagnosticSection(
        "Final Diagnosis",
        tuple(lines),
        (
            _fail(
                "NETWORK_REPAIR_REQUIRED",
                "One or more network checks failed; use the targeted repair hint.",
            ),
        ),
    )


def _repair_hints(
    diagnostics: tuple[NetworkDiagnostic, ...],
    wsl_diagnostics: tuple[NetworkDiagnostic, ...],
    runtime: RuntimeObservation,
) -> tuple[str, ...]:
    codes = {diagnostic.code for diagnostic in diagnostics}
    hints: list[str] = ["Run:", "  ./tsw doctor network"]
    if "INCUSBR0_UNAVAILABLE" in codes or "INCUS_DNSMASQ_FAILED" in codes:
        hints.extend(
            (
                "Potential repair:",
                "  ./tsw network repair --incus --apply",
            )
        )
    if "INCUS_FORWARDING_BLOCKED_BY_DOCKER" in codes or "LXC_HTTP_BLOCKED" in codes:
        hints.extend(
            (
                "Potential forwarding repair:",
                "  ./tsw network repair --linux-forwarding --apply",
            )
        )
    if runtime.is_wsl2 and runtime.networking_mode == "mirrored":
        hints.extend(
            (
                "Potential WSL runtime repair:",
                "  ./tsw network repair --runtime wsl2-nat --apply",
            )
        )
    if runtime.is_wsl2 and not wsl_diagnostics:
        hints.append("Windows portproxy checks must be run from elevated PowerShell.")
    return tuple(hints)


def _mutation_step(result: NetworkRepairMutationResult) -> NetworkRepairStep:
    if result.success:
        status = "applied" if result.applied else "skipped"
    else:
        status = "failed" if result.applied else "blocked"
    details = [*result.details]
    failed_commands = tuple(command for command in result.commands if not command.ok)
    if failed_commands:
        details.append("Failed command: " + failed_commands[-1].command)
        if failed_commands[-1].stderr:
            details.append("stderr: " + failed_commands[-1].stderr.splitlines()[-1])
    return NetworkRepairStep(result.target, status, result.message, tuple(details))


def _incus_available(observation: IncusObservation) -> bool:
    return observation.version.ok and (
        observation.network_show.ok
        or "incusbr0" in observation.network_list.stdout
    )


def _host_integration_ports(port_registry: PortRegistry) -> tuple[int, ...]:
    ports = (
        mapping.external_port
        for mapping in port_registry.mappings
        if mapping.external_port is not None
        and mapping.protocol == "tcp"
        and mapping.exposure is not PortExposureClass.PUBLIC_INGRESS
    )
    return tuple(dict.fromkeys(ports))


def _listener_ports(stdout: str) -> set[int]:
    ports: set[int] = set()
    for match in re.finditer(r":(\d{1,5})(?:\s|$)", stdout):
        value = int(match.group(1))
        if 0 < value <= 65535:
            ports.add(value)
    return ports


def _format_ports(ports: tuple[int, ...]) -> str:
    return ", ".join(str(port) for port in ports)


def _has_default_route(output: str) -> bool:
    return any(line.strip().startswith("default ") for line in output.splitlines())


def _command_missing(observation: CommandObservation) -> bool:
    output = observation.combined_output.casefold()
    return observation.return_code == 127 or "not found" in output or "no such file" in output


def _mentions_failure(value: str) -> bool:
    return any(term in value for term in ("fail", "error", "unable", "unavailable"))


def _incus_forward_rules_present(output: str) -> bool:
    return "-i incusbr0 -j ACCEPT" in output and "-o incusbr0" in output


def _incus_masquerade_present(iptables_nat: str, nft_rules: str) -> bool:
    combined = f"{iptables_nat}\n{nft_rules}".casefold()
    return "incusbr0" in combined and "masquerade" in combined


def _section_has_any(
    section: NetworkDiagnosticSection | None,
    codes: tuple[str, ...],
) -> bool:
    if section is None:
        return False
    expected = set(codes)
    return any(diagnostic.code in expected for diagnostic in section.diagnostics)


def _ok(code: str, message: str) -> NetworkDiagnostic:
    return NetworkDiagnostic(code, DiagnosticSeverity.OK, message)


def _info(code: str, message: str) -> NetworkDiagnostic:
    return NetworkDiagnostic(code, DiagnosticSeverity.INFO, message)


def _warn(code: str, message: str) -> NetworkDiagnostic:
    return NetworkDiagnostic(code, DiagnosticSeverity.WARN, message)


def _fail(code: str, message: str) -> NetworkDiagnostic:
    return NetworkDiagnostic(code, DiagnosticSeverity.FAIL, message)
