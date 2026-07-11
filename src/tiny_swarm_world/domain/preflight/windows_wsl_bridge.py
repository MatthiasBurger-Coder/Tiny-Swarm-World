from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowsWslBridgeStatus:
    prepared: bool
    reason: str
    state_path: str
    current_wsl_ip: str = ""
    state_wsl_ip: str = ""
    generated_at: str = ""
    listen_address: str = ""
    expected_ports: tuple[int, ...] = ()
    mapped_ports: tuple[int, ...] = ()
    missing_ports: tuple[int, ...] = ()
    state_age_seconds: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_ports", _sorted_ports(self.expected_ports))
        object.__setattr__(self, "mapped_ports", _sorted_ports(self.mapped_ports))
        object.__setattr__(self, "missing_ports", _sorted_ports(self.missing_ports))

    @property
    def stale(self) -> bool:
        return self.reason in {
            "state_stale_by_age",
            "wsl_ip_changed",
            "missing_ports",
            "generated_at_missing",
            "generated_at_invalid",
            "agent_contract_missing",
            "agent_not_ready",
        }


def _sorted_ports(ports: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({int(port) for port in ports}))
