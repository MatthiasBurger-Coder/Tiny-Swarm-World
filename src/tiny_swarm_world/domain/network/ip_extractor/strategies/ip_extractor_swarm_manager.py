import logging
from typing import Any

from tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_strategy import ExtractionStrategy
from tiny_swarm_world.domain.network.ip_value import IpValue


class IpExtractorSwarmManager(ExtractionStrategy):
    """Strategie zur Extraktion der Swarm-Manager-IP."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract(self, result) -> Any:
        self.logger.info(f"Extracting swarm-manager IP from: {result}")

        # If result is a list containing a dictionary, extract the dictionary
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            result = result[0]

        if not isinstance(result, dict) or 2 not in result or not isinstance(result[2], str):
            self.logger.warning("Invalid input or missing key 2.")
            return None

        return IpValue(ip_address =result[2].strip())  # Return the IP address
