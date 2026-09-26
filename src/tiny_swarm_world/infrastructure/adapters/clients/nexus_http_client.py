from tiny_swarm_world.application.ports.clients.port_nexus_client import NexusClientError
from tiny_swarm_world.application.ports.operation_result import OperationFailure
from tiny_swarm_world.infrastructure.adapters.exceptions.operation_failure_mapping import request_failure
import requests
from pydantic import ValidationError
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

    def _request(self, method: str, *args, **kwargs) -> requests.Response:
        try:
            return getattr(self.session, method)(*args, **kwargs)
        except requests.RequestException as exc:
            raise NexusClientError(request_failure(exc, "service.request", "nexus")) from None

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
        response = self._request("get",
            f"{self.base_url}/service/rest/v1/security/users",
            auth=(username, password),
            timeout=30,
        )
        self._ensure_success(response, "get Nexus users")

        payload = _response_payload(response)
        if not isinstance(payload, list) or any(not isinstance(user, dict) for user in payload):
            raise NexusClientError(OperationFailure.for_cause("service.decode", "nexus", "request_failed")) from None
        for user in payload:
            if user.get("userId") == target_user_id:
                try:
                    return NexusUser(**user)
                except ValidationError:
                    raise NexusClientError(OperationFailure.for_cause("service.decode", "nexus", "request_failed")) from None

        raise NexusClientError(OperationFailure.for_cause("service.request", "nexus", "request_failed")) from None

    def update_user(self, username: str, password: str, user: NexusUser) -> None:
        response = self._request("put",
            f"{self.base_url}/service/rest/v1/security/users/{user.userId}",
            auth=(username, password),
            json=user.model_dump(exclude_none=True),
            timeout=30,
        )
        self._ensure_success(response, f"update Nexus user '{user.userId}'")

    def change_password(self, username: str, password: str, target_user_id: str, new_password: str) -> None:
        response = self._request("put",
            f"{self.base_url}/service/rest/v1/security/users/{target_user_id}/change-password",
            auth=(username, password),
            data=new_password,
            headers={"Content-Type": "text/plain"},
            timeout=30,
        )
        self._ensure_success(response, f"change password for Nexus user '{target_user_id}'")

    def set_anonymous_access(self, username: str, password: str, enabled: bool) -> None:
        response = self._request("put",
            f"{self.base_url}/service/rest/v1/security/anonymous",
            auth=(username, password),
            json={"enabled": enabled},
            timeout=30,
        )
        self._ensure_success(response, "update Nexus anonymous access")

    def repository_exists(self, username: str, password: str, repository_name: str) -> bool:
        response = self._request("get",
            f"{self.base_url}/service/rest/v1/repositories",
            auth=(username, password),
            timeout=30,
        )
        self._ensure_success(response, "list Nexus repositories")

        repositories = _response_payload(response)
        if not isinstance(repositories, list):
            raise NexusClientError(OperationFailure.for_cause("service.request", "nexus", "request_failed")) from None
        return any(repository.get("name") == repository_name for repository in repositories if isinstance(repository, dict))

    def create_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        response = self._request("post",
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
        response = self._request("put",
            f"{self.base_url}/service/rest/v1/repositories/docker/hosted/{repository_name}",
            auth=(username, password),
            json=_docker_hosted_repository_payload(repository_name, http_port),
            timeout=30,
        )
        self._ensure_success(response, f"update Nexus Docker hosted repository '{repository_name}'")

    def create_docker_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
        remote_url: str,
    ) -> None:
        response = self._request("post",
            f"{self.base_url}/service/rest/v1/repositories/docker/proxy",
            auth=(username, password),
            json=_docker_proxy_repository_payload(repository_name, http_port, remote_url),
            timeout=30,
        )
        self._ensure_success(response, f"create Nexus Docker proxy repository '{repository_name}'")

    def create_maven_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        remote_url: str,
    ) -> None:
        response = self._request("post",
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
            raise NexusClientError(OperationFailure.for_cause("service.request", "nexus", "request_failed"), status_code=response.status_code) from None


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


def _docker_proxy_repository_payload(
    repository_name: str,
    http_port: int,
    remote_url: str,
) -> dict[str, object]:
    return {
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
        "docker": {
            "v1Enabled": False,
            "forceBasicAuth": False,
            "httpPort": http_port,
        },
        "dockerProxy": {
            "indexType": "HUB",
        },
    }


def _response_payload(response: requests.Response):
    try:
        return response.json()
    except ValueError:
        raise NexusClientError(OperationFailure.for_cause("service.decode", "nexus", "request_failed")) from None
