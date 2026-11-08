import logging
from ipaddress import IPv4Address

from tiny_swarm_world.domain.network.socat.docker_ip_list import DockerIpList
from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_strategy import ExtractionStrategy
from tiny_swarm_world.domain.network.ip_value import IpValue


PLACEHOLDER_NODE_IP = str(IPv4Address(0x01010101))


class IpExtractorSwarmNodeIpList(ExtractionStrategy):

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract(self, result) -> DockerIpList:
        external_ip = IpValue(ip_address=PLACEHOLDER_NODE_IP)
        docker_bridge_ip = IpValue(ip_address=PLACEHOLDER_NODE_IP)
        docker_overlay_ip = IpValue(ip_address=PLACEHOLDER_NODE_IP)
        gateway = IpValue(ip_address=PLACEHOLDER_NODE_IP)

        return DockerIpList(external_ip=external_ip, docker_bridge_ip=docker_bridge_ip, docker_overlay_ip=docker_overlay_ip, gateway=gateway)
