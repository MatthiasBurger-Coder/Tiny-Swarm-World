import requests
from urllib.parse import urlparse

from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.domain.nexus.nexus_user import NexusUser
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class NexusHttpClient(PortNexusClient):
    def __init__(self, base_url: str, session: requests.Session | None = None):
        parsed_url = urlparse(base_url)
        if parsed_url.username or parsed_url.password:
            raise ValueError("Nexus base URL must not contain credentials.")
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.logger = LoggerFactory.get_logger(self.__class__)

    def is_available(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/service/rest/v1/status", timeout=30)
        except requests.RequestException:
            return False
        return response.status_code == 200

    def can_authenticate(self, username: str, password: str) -> bool:
        try:
            response = self.session.get(
                f"{self.base_url}/service/rest/v1/security/users",
                auth=(username, password),
                timeout=30,
            )
        except requests.RequestException:
            return False
        return response.status_code == 200

    def get_user(self, username: str, password: str, target_user_id: str) -> NexusUser:
        try:
            response = self.session.get(
                f"{self.base_url}/service/rest/v1/security/users",
                auth=(username, password),
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError("Failed to get Nexus users with redacted output.") from exc
        self._ensure_success(response, "get Nexus users")

        for user in response.json():
            if user.get("userId") == target_user_id:
                return NexusUser(**user)

        raise RuntimeError(f"Nexus user '{target_user_id}' was not found.")

    def update_user(self, username: str, password: str, user: NexusUser) -> None:
        try:
            response = self.session.put(
                f"{self.base_url}/service/rest/v1/security/users/{user.userId}",
                auth=(username, password),
                json=user.model_dump(exclude_none=True),
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to update Nexus user '{user.userId}' with redacted output.") from exc
        self._ensure_success(response, f"update Nexus user '{user.userId}'")

    def change_password(self, username: str, password: str, target_user_id: str, new_password: str) -> None:
        try:
            response = self.session.put(
                f"{self.base_url}/service/rest/v1/security/users/{target_user_id}/change-password",
                auth=(username, password),
                data=new_password,
                headers={"Content-Type": "text/plain"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to change password for Nexus user '{target_user_id}' with redacted output."
            ) from exc
        self._ensure_success(response, f"change password for Nexus user '{target_user_id}'")

    def set_anonymous_access(self, username: str, password: str, enabled: bool) -> None:
        response = self.session.put(
            f"{self.base_url}/service/rest/v1/security/anonymous",
            auth=(username, password),
            json={"enabled": enabled},
            timeout=30,
        )
        self._ensure_success(response, "update Nexus anonymous access")

    def repository_exists(self, username: str, password: str, repository_name: str) -> bool:
        response = self.session.get(
            f"{self.base_url}/service/rest/v1/repositories",
            auth=(username, password),
            timeout=30,
        )
        self._ensure_success(response, "list Nexus repositories")

        repositories = response.json()
        if not isinstance(repositories, list):
            raise RuntimeError("Nexus repository listing returned an unexpected payload.")
        return any(repository.get("name") == repository_name for repository in repositories if isinstance(repository, dict))

    def create_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        response = self.session.post(
            f"{self.base_url}/service/rest/v1/repositories/docker/hosted",
            auth=(username, password),
            json=_docker_hosted_repository_payload(repository_name, http_port),
            timeout=30,
        )
        self._ensure_success(response, f"create Nexus Docker hosted repository '{repository_name}'")

    def update_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        response = self.session.put(
            f"{self.base_url}/service/rest/v1/repositories/docker/hosted/{repository_name}",
            auth=(username, password),
            json=_docker_hosted_repository_payload(repository_name, http_port),
            timeout=30,
        )
        self._ensure_success(response, f"update Nexus Docker hosted repository '{repository_name}'")

    def create_maven_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        remote_url: str,
    ) -> None:
        response = self.session.post(
            f"{self.base_url}/service/rest/v1/repositories/maven/proxy",
            auth=(username, password),
            json={
                "name": repository_name,
                "online": True,
                "storage": {
                    "blobStoreName": "default",
                    "strictContentTypeValidation": True,
                },
                "proxy": {
                    "remoteUrl": remote_url,
                    "contentMaxAge": 1440,
                    "metadataMaxAge": 1440,
                },
                "negativeCache": {
                    "enabled": True,
                    "timeToLive": 1440,
                },
                "httpClient": {
                    "blocked": False,
                    "autoBlock": True,
                },
                "maven": {
                    "versionPolicy": "RELEASE",
                    "layoutPolicy": "STRICT",
                },
            },
            timeout=30,
        )
        self._ensure_success(response, f"create Nexus Maven proxy repository '{repository_name}'")

    @staticmethod
    def _ensure_success(response: requests.Response, action: str) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"Failed to {action}. HTTP {response.status_code}.")


def _docker_hosted_repository_payload(repository_name: str, http_port: int) -> dict[str, object]:
    return {
        "name": repository_name,
        "online": True,
        "storage": {
            "blobStoreName": "default",
            "strictContentTypeValidation": True,
            "writePolicy": "ALLOW",
        },
        "docker": {
            "v1Enabled": False,
            "forceBasicAuth": True,
            "httpPort": http_port,
        },
    }
