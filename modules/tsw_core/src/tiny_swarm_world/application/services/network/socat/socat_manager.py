from __future__ import annotations

import logging
import shlex
from dataclasses import dataclass

from tiny_swarm_world.domain.network.port_forwarding_plan import (
    ForwardingStrategy,
    PortForwardingPlan,
)


@dataclass(frozen=True)
class SocatForwardingCommand:
    plan: PortForwardingPlan
    listen_address: str
    target_host: str

    @property
    def argv(self) -> tuple[str, ...]:
        return (
            "socat",
            (
                f"TCP-LISTEN:{self.plan.listen_port},"
                f"fork,reuseaddr,bind={self.listen_address}"
            ),
            f"TCP:{self.target_host}:{self.plan.target_port}",
        )

    @property
    def shell_command(self) -> str:
        return " ".join(shlex.quote(part) for part in self.argv)


class SocatManager:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_service_socat_ports(
        self,
        os_type: object,
        plans: tuple[PortForwardingPlan, ...],
        *,
        listen_address: str = "0.0.0.0",
        target_host: str = "127.0.0.1",
    ) -> tuple[SocatForwardingCommand, ...]:
        if _os_type_value(os_type) != "wsl_linux":
            return ()
        return tuple(
            SocatForwardingCommand(
                plan=plan,
                listen_address=listen_address,
                target_host=target_host,
            )
            for plan in plans
            if plan.strategy is ForwardingStrategy.WSL2_SOCAT
        )


def _os_type_value(os_type: object) -> str:
    return str(getattr(os_type, "value", os_type)).lower()
