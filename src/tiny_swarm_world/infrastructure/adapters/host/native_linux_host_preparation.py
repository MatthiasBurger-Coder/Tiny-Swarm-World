from __future__ import annotations

from pathlib import Path

from tiny_swarm_world.application.ports.host import PortHostPreparation
from tiny_swarm_world.domain.preflight import HostPreparationResult, HostPreparationStatus


_REQUIRED_KERNEL_CONTROLS = {
    "net.bridge.bridge-nf-call-iptables": Path("net/bridge/bridge-nf-call-iptables"),
    "net.bridge.bridge-nf-call-ip6tables": Path("net/bridge/bridge-nf-call-ip6tables"),
    "net.ipv4.ip_forward": Path("net/ipv4/ip_forward"),
}


class NativeLinuxHostPreparation(PortHostPreparation):
    """Verify required native-Linux kernel controls without changing them."""

    def __init__(self, *, proc_sys_root: Path = Path("/proc/sys")) -> None:
        self._proc_sys_root = proc_sys_root

    def prepare(self) -> HostPreparationResult:
        return self._verification_result("prepare")

    def verify(self) -> HostPreparationResult:
        return self._verification_result("verify")

    def cleanup(self) -> HostPreparationResult:
        return HostPreparationResult(
            "cleanup",
            "native_linux",
            HostPreparationStatus.SUCCESS,
            "Operator-owned native Linux kernel state was left unchanged.",
            changed=False,
            verified=False,
            evidence={},
        )

    def _verification_result(self, operation: str) -> HostPreparationResult:
        evidence = {
            control_name: self._read_control_status(relative_path)
            for control_name, relative_path in _REQUIRED_KERNEL_CONTROLS.items()
        }
        ready = all(status == "active" for status in evidence.values())
        return HostPreparationResult(
            operation,
            "native_linux",
            HostPreparationStatus.SUCCESS if ready else HostPreparationStatus.FAILED,
            (
                "Required native Linux kernel controls are active."
                if ready
                else "Required native Linux kernel controls are not ready; apply the "
                "documented temporary activation and persistence steps, then retry."
            ),
            changed=False,
            verified=ready,
            evidence=evidence,
        )

    def _read_control_status(self, relative_path: Path) -> str:
        try:
            value = (self._proc_sys_root / relative_path).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return "missing"
        except OSError:
            return "read_error"
        return "active" if value == "1" else "disabled"
