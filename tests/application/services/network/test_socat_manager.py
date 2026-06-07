import unittest

from tiny_swarm_world.application.services.network.socat.socat_manager import SocatManager
from tiny_swarm_world.domain.network.port_forwarding_plan import (
    ForwardingStrategy,
    PortForwardingPlan,
)
from tiny_swarm_world.infrastructure.os_types import OsTypes


class TestSocatManager(unittest.TestCase):
    def test_wsl_linux_creates_socat_forwarding_commands(self):
        manager = SocatManager()
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.WSL2_SOCAT,
            service="Portainer",
            listen_port=9000,
            target_port=9000,
        )

        commands = manager.set_service_socat_ports(OsTypes.WSL_LINUX, (plan,))

        self.assertEqual(1, len(commands))
        self.assertEqual(
            (
                "socat",
                "TCP-LISTEN:9000,fork,reuseaddr,bind=0.0.0.0",
                "TCP:127.0.0.1:9000",
            ),
            commands[0].argv,
        )

    def test_non_wsl_linux_does_not_create_socat_commands(self):
        manager = SocatManager()
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.WSL2_SOCAT,
            service="Portainer",
            listen_port=9000,
            target_port=9000,
        )

        self.assertEqual((), manager.set_service_socat_ports(OsTypes.LINUX, (plan,)))
        self.assertEqual((), manager.set_service_socat_ports(OsTypes.WINDOWS, (plan,)))

    def test_wsl_linux_ignores_non_socat_plans(self):
        manager = SocatManager()
        plan = PortForwardingPlan(
            strategy=ForwardingStrategy.NATIVE_LINUX_DIRECT,
            service="Portainer",
            listen_port=9000,
            target_port=9000,
        )

        self.assertEqual((), manager.set_service_socat_ports(OsTypes.WSL_LINUX, (plan,)))


if __name__ == "__main__":
    unittest.main()
