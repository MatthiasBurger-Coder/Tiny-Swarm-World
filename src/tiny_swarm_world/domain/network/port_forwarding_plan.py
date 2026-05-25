from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ForwardingStrategy(str, Enum):
    NATIVE_LINUX_DIRECT = "native_linux_direct"
    WSL2_SOCAT = "wsl2_socat"
    WSL2_NETSH_DOCUMENTED = "wsl2_netsh_documented"
    WSL2_IPTABLES_OPTIONAL = "wsl2_iptables_optional"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class PortForwardingPlan:
    strategy: ForwardingStrategy
    service: str
    listen_port: int
    target_port: int
    remediation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.service.strip():
            raise ValueError("service cannot be empty")
        _validate_port(self.listen_port, "listen_port")
        _validate_port(self.target_port, "target_port")
        object.__setattr__(self, "service", self.service.strip())
        object.__setattr__(self, "remediation", tuple(self.remediation))

    @property
    def requires_operator_action(self) -> bool:
        return self.strategy in {
            ForwardingStrategy.WSL2_SOCAT,
            ForwardingStrategy.WSL2_NETSH_DOCUMENTED,
            ForwardingStrategy.WSL2_IPTABLES_OPTIONAL,
        }

    @property
    def supported_without_operator_action(self) -> bool:
        return self.strategy == ForwardingStrategy.NATIVE_LINUX_DIRECT

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy": self.strategy.value,
            "service": self.service,
            "listen_port": self.listen_port,
            "target_port": self.target_port,
            "requires_operator_action": self.requires_operator_action,
            "supported_without_operator_action": self.supported_without_operator_action,
            "remediation": list(self.remediation),
        }


def _validate_port(value: int, field_name: str) -> None:
    if not isinstance(value, int) or value < 1 or value > 65535:
        raise ValueError(f"{field_name} must be a TCP port between 1 and 65535")
