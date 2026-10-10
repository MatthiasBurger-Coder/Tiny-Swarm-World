"""Policy for the separately invoked native Linux host preparation step."""

from __future__ import annotations

from dataclasses import dataclass


GIB = 1024**3
MINIMUM_CPUS = 4
MINIMUM_MEMORY_BYTES = 16 * GIB
MINIMUM_FREE_DISK_BYTES = 60 * GIB
PROFILE_MINIMUM_CPUS = {"default": MINIMUM_CPUS, "service-access": 8}
PROFILE_MINIMUM_MEMORY_BYTES = {
    "default": MINIMUM_MEMORY_BYTES,
    # Host qualification is separate from managed-node capacity checks.
    "service-access": 15 * GIB,
}
PROFILE_MINIMUM_FREE_DISK_BYTES = {
    "default": MINIMUM_FREE_DISK_BYTES,
    "service-access": 150 * GIB,
}
SUPPORTED_UBUNTU_RELEASES = ("24.04", "26.04")
HOST_PACKAGES = (
    "ca-certificates",
    "curl",
    "dnsmasq-base",
    "git",
    "incus",
    "iptables",
    "iproute2",
    "jq",
    "kmod",
    "nftables",
    "openssl",
    "python3",
    "python3-venv",
)
HOST_PACKAGES_BY_PROFILE = {
    "default": HOST_PACKAGES,
    "service-access": HOST_PACKAGES,
}
HOST_PORTS_BY_PROFILE = {
    "default": (10001, 13081, 13500, 13501, 11080, 11050, 14001, 14080, 14081, 7750, 12000, 16080, 16081),
    "service-access": (80, 443),
}


@dataclass(frozen=True)
class NativeHostFacts:
    platform: str
    is_wsl: bool
    distribution_id: str
    version_id: str
    architecture: str
    cpu_count: int
    memory_bytes: int
    free_disk_bytes: int
    can_install_packages: bool
    repository_writable: bool
    kernel_ready: bool
    ports_ready: bool
    conflicting_runtime: bool
    network_ready: bool
    wsl2: bool = False
    systemd_ready: bool = True


def qualification_failures(
    facts: NativeHostFacts, *, needs_network: bool, needs_ports: bool = True,
    needs_privilege: bool = True, service_profile: str = "service-access",
    prerequisites_only: bool = False, allow_wsl: bool = False,
) -> tuple[str, ...]:
    """Return stable, operator-actionable findings without host-specific data."""
    failures: list[str] = []
    if facts.platform != "Linux" or (facts.is_wsl and not allow_wsl):
        failures.append("Native Linux is required; WSL and other operating systems are unsupported.")
    if facts.distribution_id != "ubuntu" or facts.version_id not in SUPPORTED_UBUNTU_RELEASES:
        failures.append("Ubuntu 24.04 or 26.04 LTS is required for native host preparation.")
    if facts.architecture != "x86_64":
        failures.append("x86_64 is required for the qualified native profile.")
    minimum_cpus = PROFILE_MINIMUM_CPUS[service_profile]
    if facts.is_wsl and allow_wsl and (not facts.wsl2 or not facts.systemd_ready):
        failures.append("WSL2 with systemd is required for Ubuntu prerequisite preparation.")
    minimum_memory = PROFILE_MINIMUM_MEMORY_BYTES[service_profile]
    if facts.is_wsl:
        minimum_memory = max(minimum_memory, 16 * GIB)
    minimum_disk = PROFILE_MINIMUM_FREE_DISK_BYTES[service_profile]
    if facts.cpu_count < minimum_cpus:
        failures.append(f"At least {minimum_cpus} CPU threads are required for {service_profile}.")
    if facts.memory_bytes < minimum_memory:
        failures.append(
            f"At least {minimum_memory // GIB} GiB of RAM is required for {service_profile}."
        )
    if facts.free_disk_bytes < minimum_disk:
        failures.append(
            f"At least {minimum_disk // GIB} GiB of free disk space is required for {service_profile}."
        )
    if needs_privilege and not facts.can_install_packages:
        failures.append("Root or active sudo APT permission is required; run sudo -v and retry.")
    if not facts.repository_writable:
        failures.append("The repository target must be writable by the operator.")
    if not prerequisites_only and not facts.kernel_ready:
        failures.append("Required Linux bridge and IPv4 forwarding controls are unavailable.")
    if not prerequisites_only and needs_ports and not facts.ports_ready:
        failures.append("A required host port is occupied by an unrecognized service.")
    if facts.conflicting_runtime:
        failures.append("A conflicting host container runtime is active; resolve it manually.")
    if needs_network and not facts.network_ready:
        failures.append("DNS or HTTPS connectivity to Ubuntu package sources is unavailable.")
    return tuple(failures)


def preparation_target(facts: NativeHostFacts) -> tuple[object, ...]:
    """Stable target identity; live capacity is requalified separately."""
    return (facts.platform, facts.is_wsl, facts.distribution_id, facts.version_id,
            facts.architecture, facts.wsl2, facts.systemd_ready)
