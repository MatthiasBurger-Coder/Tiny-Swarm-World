import logging
import time

from tiny_swarm_world.application.ports.clients.port_container_runtime import PortContainerRuntime
from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient


class EnsureNexusAdminAccess:
    def __init__(
        self,
        nexus_client: PortNexusClient,
        container_runtime: PortContainerRuntime,
        admin_username: str,
        admin_password: str,
        container_name_filter: str,
        initial_password_path: str,
        max_attempts: int,
        wait_seconds: int,
    ):
        self.nexus_client = nexus_client
        self.container_runtime = container_runtime
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.container_name_filter = container_name_filter
        self.initial_password_path = initial_password_path
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        if self.nexus_client.can_authenticate(self.admin_username, self.admin_password):
            self.logger.info("Nexus admin credentials are already active.")
            return

        container_name = self._resolve_container_name()
        initial_password = self._read_initial_password(container_name)

        admin_user = self.nexus_client.get_user(self.admin_username, initial_password, self.admin_username)
        if admin_user.status != "active":
            self.logger.info("Activating Nexus admin user.")
            self.nexus_client.update_user(
                self.admin_username,
                initial_password,
                admin_user.model_copy(update={"status": "active"}),
            )

        self.logger.info("Rotating Nexus admin password.")
        self.nexus_client.change_password(
            self.admin_username,
            initial_password,
            self.admin_username,
            self.admin_password,
        )

        if not self.nexus_client.can_authenticate(self.admin_username, self.admin_password):
            raise RuntimeError("Nexus admin password rotation completed without producing valid credentials.")

    def _resolve_container_name(self) -> str:
        for attempt in range(1, self.max_attempts + 1):
            container_names = self.container_runtime.find_container_names(self.container_name_filter)
            if container_names:
                container_name = sorted(container_names)[0]
                self.logger.info(f"Using Nexus container '{container_name}'.")
                return container_name

            if attempt < self.max_attempts:
                self.logger.info(
                    f"No Nexus container matched '{self.container_name_filter}'. "
                    f"Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise RuntimeError(f"No container found for filter '{self.container_name_filter}'.")

    def _read_initial_password(self, container_name: str) -> str:
        for attempt in range(1, self.max_attempts + 1):
            if self.container_runtime.file_exists(container_name, self.initial_password_path):
                password = self.container_runtime.read_file(container_name, self.initial_password_path).strip()
                if password:
                    self.logger.info("Read initial Nexus admin password from container.")
                    return password

            if attempt < self.max_attempts:
                self.logger.info(
                    f"Initial password file '{self.initial_password_path}' is not available yet. "
                    f"Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise RuntimeError(f"Could not read Nexus admin password from '{self.initial_password_path}'.")
