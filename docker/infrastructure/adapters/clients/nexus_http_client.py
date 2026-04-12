import requests

from application.ports.clients.port_nexus_client import PortNexusClient
from domain.nexus.nexus_user import NexusUser
from infrastructure.logging.logger_factory import LoggerFactory


class NexusHttpClient(PortNexusClient):
    def __init__(self, base_url: str, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.logger = LoggerFactory.get_logger(self.__class__)

    def is_available(self) -> bool:
        response = self.session.get(f"{self.base_url}/service/rest/v1/status", timeout=30)
        return response.status_code == 200

    def can_authenticate(self, username: str, password: str) -> bool:
        response = self.session.get(
            f"{self.base_url}/service/rest/v1/security/users",
            auth=(username, password),
            timeout=30,
        )
        return response.status_code == 200

    def get_user(self, username: str, password: str, target_user_id: str) -> NexusUser:
        response = self.session.get(
            f"{self.base_url}/service/rest/v1/security/users",
            auth=(username, password),
            timeout=30,
        )
        self._ensure_success(response, "get Nexus users")

        for user in response.json():
            if user.get("userId") == target_user_id:
                return NexusUser(**user)

        raise RuntimeError(f"Nexus user '{target_user_id}' was not found.")

    def update_user(self, username: str, password: str, user: NexusUser) -> None:
        response = self.session.put(
            f"{self.base_url}/service/rest/v1/security/users/{user.userId}",
            auth=(username, password),
            json=user.model_dump(exclude_none=True),
            timeout=30,
        )
        self._ensure_success(response, f"update Nexus user '{user.userId}'")

    def change_password(self, username: str, password: str, target_user_id: str, new_password: str) -> None:
        response = self.session.put(
            f"{self.base_url}/service/rest/v1/security/users/{target_user_id}/change-password",
            auth=(username, password),
            data=new_password,
            headers={"Content-Type": "text/plain"},
            timeout=30,
        )
        self._ensure_success(response, f"change password for Nexus user '{target_user_id}'")

    def set_anonymous_access(self, username: str, password: str, enabled: bool) -> None:
        response = self.session.put(
            f"{self.base_url}/service/rest/v1/security/anonymous",
            auth=(username, password),
            json={"enabled": enabled},
            timeout=30,
        )
        self._ensure_success(response, "update Nexus anonymous access")

    @staticmethod
    def _ensure_success(response: requests.Response, action: str) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"Failed to {action}. HTTP {response.status_code}: {response.text}")
