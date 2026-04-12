from application.ports.clients.port_nexus_client import PortNexusClient
from infrastructure.logging.logger_factory import LoggerFactory


class EnableNexusAnonymousAccess:
    def __init__(self, nexus_client: PortNexusClient, admin_username: str, admin_password: str):
        self.nexus_client = nexus_client
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.logger = LoggerFactory.get_logger(self.__class__)

    def run(self) -> None:
        self.logger.info("Enabling anonymous access in Nexus.")
        self.nexus_client.set_anonymous_access(self.admin_username, self.admin_password, enabled=True)
