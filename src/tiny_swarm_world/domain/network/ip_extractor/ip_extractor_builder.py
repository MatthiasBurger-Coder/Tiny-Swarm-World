from typing import Any

from tiny_swarm_world.domain.network.ip_extractor.strategies.IpExtractorSwarmNodeIpList import IpExtractorSwarmNodeIpList
from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_gateway import IpExtractorGateway
from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_swarm_manager import IpExtractorSwarmManager
from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extstractor_types import IpExtractorTypes
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class IpExtractorBuilder:

    def __init__(self):
        self.logger = LoggerFactory.get_logger(self.__class__)

        self.STRATEGY_MAP = {
            IpExtractorTypes.GATEWAY: IpExtractorGateway(),
            IpExtractorTypes.SWAM_MANAGER: IpExtractorSwarmManager(),
            IpExtractorTypes.NONE: None,
            IpExtractorTypes.SWARM_NODE_IP_LIST: IpExtractorSwarmNodeIpList()
        }

    def build(self, result:str, ip_extractor_types: IpExtractorTypes) -> Any:
        self.logger.info(f"Building ip extractor strategy for type: {ip_extractor_types}")
        strategy = self.STRATEGY_MAP.get(ip_extractor_types)
        return strategy.extract(result)
