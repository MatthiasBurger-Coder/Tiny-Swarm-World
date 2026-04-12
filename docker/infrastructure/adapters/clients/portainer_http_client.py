import requests

from application.ports.clients.port_portainer_client import PortPortainerClient
from domain.deployment.stack_definition import StackDefinition
from infrastructure.logging.logger_factory import LoggerFactory


class PortainerHttpClient(PortPortainerClient):
    def __init__(self, base_url: str, username: str, password: str, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.logger = LoggerFactory.get_logger(self.__class__)
        self._jwt_token: str | None = None

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        response = self._send("GET", "/api/endpoints")
        self._ensure_success(response, f"fetch Portainer endpoint '{endpoint_name}'")

        for endpoint in response.json():
            if endpoint.get("Name") == endpoint_name:
                return int(endpoint["Id"])

        raise RuntimeError(f"Portainer endpoint '{endpoint_name}' was not found.")

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        response = self._send("GET", "/api/stacks")
        self._ensure_success(response, f"fetch Portainer stack '{stack_name}'")

        for stack in response.json():
            if stack.get("Name") == stack_name:
                return int(stack["Id"])
        return None

    def create_stack(self, stack_definition: StackDefinition, endpoint_id: int) -> None:
        payload = {
            "env": [],
            "name": stack_definition.name,
            "fromAppTemplate": False,
            "stackFileContent": stack_definition.compose_content,
        }

        response = self._send(
            "POST",
            f"/api/stacks/create/swarm/string?endpointId={endpoint_id}",
            json=payload,
        )
        if response.status_code in {404, 405}:
            response = self._send(
                "POST",
                "/api/stacks",
                json={**payload, "endpointId": endpoint_id},
            )

        self._ensure_success(response, f"create Portainer stack '{stack_definition.name}'")

    def update_stack(self, stack_id: int, stack_definition: StackDefinition, endpoint_id: int) -> None:
        response = self._send(
            "PUT",
            f"/api/stacks/{stack_id}?endpointId={endpoint_id}",
            json={
                "env": [],
                "prune": True,
                "pullImage": False,
                "stackFileContent": stack_definition.compose_content,
            },
        )
        self._ensure_success(response, f"update Portainer stack '{stack_definition.name}'")

    def _send(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._get_jwt_token()}"
        return self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=30,
            **kwargs,
        )

    def _get_jwt_token(self) -> str:
        if self._jwt_token is not None:
            return self._jwt_token

        response = self.session.post(
            f"{self.base_url}/api/auth",
            json={"Username": self.username, "Password": self.password},
            timeout=30,
        )
        self._ensure_success(response, "authenticate against Portainer")

        token = response.json().get("jwt")
        if not token:
            raise RuntimeError("Portainer authentication succeeded without returning a JWT.")

        self._jwt_token = token
        return token

    @staticmethod
    def _ensure_success(response: requests.Response, action: str) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"Failed to {action}. HTTP {response.status_code}: {response.text}")
