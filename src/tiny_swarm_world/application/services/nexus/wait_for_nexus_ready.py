import logging
import time

from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient


class WaitForNexusReady:
    def __init__(self, nexus_client: PortNexusClient, max_attempts: int, wait_seconds: int):
        self.nexus_client = nexus_client
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self.nexus_client.is_available():
                self.logger.info(f"Nexus became ready on attempt {attempt}.")
                return

            if attempt < self.max_attempts:
                self.logger.info(
                    f"Nexus is not ready yet. Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise TimeoutError(
            f"Nexus did not become ready after {self.max_attempts} attempts with {self.wait_seconds} seconds delay."
        )
