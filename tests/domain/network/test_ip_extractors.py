import unittest

from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_swarm_manager import (
    IpExtractorSwarmManager,
)
from tiny_swarm_world.domain.network.ip_value import IpValue


class TestIpExtractors(unittest.TestCase):
    def test_swarm_manager_extractor_uses_first_ipv4_from_hostname_output(self):
        result = [{1: "default via 10.34.157.1 dev ens3", 2: "10.34.157.147 172.17.0.1 172.18.0.1"}]

        extracted = IpExtractorSwarmManager().extract(result)

        self.assertEqual(IpValue(ip_address="10.34.157.147"), extracted)
