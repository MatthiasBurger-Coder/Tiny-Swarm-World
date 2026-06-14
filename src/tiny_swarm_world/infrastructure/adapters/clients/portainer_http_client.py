from collections.abc import Mapping, Sequence
from urllib.parse import urlparse

import requests

from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
    PortDeploymentGateway,
)
from tiny_swarm_world.application.ports.clients.port_portainer_client import PortPortainerClient
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class PortainerHttpClient(PortPortainerClient, PortDeploymentGateway):
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        session: requests.Session | None = None,
        request_timeout_seconds: int = 30,
        stack_request_timeout_seconds: int = 180,
        deployment_endpoint_name: str = "local",
    ):
        parsed_base_url = urlparse(base_url)
        if parsed_base_url.username or parsed_base_url.password:
            raise ValueError("Portainer base URL must not contain credentials")
        if request_timeout_seconds <= 0:
            raise ValueError("Portainer request timeout must be positive")
        if stack_request_timeout_seconds <= 0:
            raise ValueError("Portainer stack request timeout must be positive")

        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.request_timeout_seconds = request_timeout_seconds
        self.stack_request_timeout_seconds = stack_request_timeout_seconds
        self.deployment_endpoint_name = deployment_endpoint_name
        self.logger = LoggerFactory.get_logger(self.__class__)
        self._jwt_token: str | None = None

    def ensure_local_endpoint(self, endpoint_name: str) -> int:
        endpoints = self._fetch_endpoints(f"ensure Portainer endpoint '{endpoint_name}'")
        endpoint_id = _endpoint_id_by_name_or_local_fallback(endpoint_name, endpoints)
        if endpoint_id is not None:
            return endpoint_id

        self._create_local_docker_endpoint(endpoint_name)
        endpoints = self._fetch_endpoints(f"verify Portainer endpoint '{endpoint_name}'")
        endpoint_id = _endpoint_id_by_name_or_local_fallback(endpoint_name, endpoints)
        if endpoint_id is None:
            raise RuntimeError(
                f"Portainer endpoint '{endpoint_name}' could not be created. "
                f"Available endpoints: {_available_endpoint_names(endpoints)}."
            )
        return endpoint_id

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        endpoints = self._fetch_endpoints(f"fetch Portainer endpoint '{endpoint_name}'")
        endpoint_id = _endpoint_id_by_name_or_local_fallback(endpoint_name, endpoints)
        if endpoint_id is not None:
            return endpoint_id

        raise RuntimeError(
            f"Portainer endpoint '{endpoint_name}' was not found. "
            f"Available endpoints: {_available_endpoint_names(endpoints)}."
        )

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        response = self._send("GET", "/api/stacks")
        self._ensure_success(response, f"fetch Portainer stack '{stack_name}'")

        for stack in response.json():
            if stack.get("Name") == stack_name:
                return int(stack["Id"])
        return None

    def create_stack(
        self,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        swarm_id = self._get_swarm_id_by_endpoint_id(endpoint_id)
        payload = {
            "env": _portainer_environment(stack_environment),
            "name": stack_definition.name,
            "fromAppTemplate": False,
            "stackFileContent": stack_definition.compose_content,
            "SwarmID": swarm_id,
        }

        response = self._send(
            "POST",
            f"/api/stacks/create/swarm/string?endpointId={endpoint_id}",
            timeout=self.stack_request_timeout_seconds,
            json=payload,
        )
        if response.status_code in {404, 405}:
            response = self._send(
                "POST",
                "/api/stacks",
                timeout=self.stack_request_timeout_seconds,
                json={**payload, "endpointId": endpoint_id},
            )

        self._ensure_success(response, f"create Portainer stack '{stack_definition.name}'")

    def update_stack(
        self,
        stack_id: int,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        response = self._send(
            "PUT",
            f"/api/stacks/{stack_id}?endpointId={endpoint_id}",
            timeout=self.stack_request_timeout_seconds,
            json={
                "env": _portainer_environment(stack_environment),
                "prune": True,
                "pullImage": False,
                "stackFileContent": stack_definition.compose_content,
            },
        )
        self._ensure_success(response, f"update Portainer stack '{stack_definition.name}'")

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        endpoint_id = self.get_endpoint_id_by_name(self.deployment_endpoint_name)
        stack_id = self.find_stack_id_by_name(request.stack_definition.name)
        if stack_id is None:
            self.create_stack(
                request.stack_definition,
                endpoint_id,
                request.stack_environment,
            )
            return
        self.update_stack(
            stack_id,
            request.stack_definition,
            endpoint_id,
            request.stack_environment,
        )

    def stack_registered(self, stack_name: str) -> bool:
        return self.find_stack_id_by_name(stack_name) is not None

    def _fetch_endpoints(self, action: str) -> tuple[Mapping[str, object], ...]:
        response = self._send("GET", "/api/endpoints")
        self._ensure_success(response, action)
        return _endpoint_mappings(response.json())

    def _create_local_docker_endpoint(self, endpoint_name: str) -> None:
        response = self._send(
            "POST",
            "/api/endpoints",
            files={
                "Name": (None, endpoint_name),
                "EndpointCreationType": (None, "1"),
                "ContainerEngine": (None, "docker"),
                "URL": (None, "unix:///var/run/docker.sock"),
            },
        )
        self._ensure_success(response, f"create Portainer endpoint '{endpoint_name}'")

    def _send(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", {})
        timeout_seconds = kwargs.pop("timeout", self.request_timeout_seconds)
        headers["Authorization"] = f"Bearer {self._get_jwt_token()}"
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=dict(headers),
            timeout=timeout_seconds,
            **kwargs,
        )
        if response.status_code != 401:
            return response

        self._jwt_token = None
        headers["Authorization"] = f"Bearer {self._get_jwt_token()}"
        return self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=dict(headers),
            timeout=timeout_seconds,
            **kwargs,
        )

    def _get_jwt_token(self) -> str:
        if self._jwt_token is not None:
            return self._jwt_token

        response = self.session.post(
            f"{self.base_url}/api/auth",
            json={"Username": self.username, "Password": self.password},
            timeout=self.request_timeout_seconds,
        )
        self._ensure_success(response, "authenticate against Portainer")

        token = response.json().get("jwt")
        if not token:
            raise RuntimeError("Portainer authentication succeeded without returning a JWT.")

        self._jwt_token = token
        self._clear_session_cookies()
        return token

    def _clear_session_cookies(self) -> None:
        cookies = getattr(self.session, "cookies", None)
        clear = getattr(cookies, "clear", None)
        if callable(clear):
            clear()

    def _get_swarm_id_by_endpoint_id(self, endpoint_id: int) -> str:
        response = self._send("GET", f"/api/endpoints/{endpoint_id}/docker/info")
        self._ensure_success(response, f"fetch Swarm identity for Portainer endpoint '{endpoint_id}'")
        swarm_id = _extract_swarm_id(response.json())
        if not swarm_id:
            raise RuntimeError(
                f"Portainer endpoint '{endpoint_id}' did not report a Swarm cluster ID."
            )
        return swarm_id

    @staticmethod
    def _ensure_success(response: requests.Response, action: str) -> None:
        if response.status_code >= 400:
            raise RuntimeError(f"Failed to {action}. HTTP {response.status_code}.")


def _portainer_environment(
    stack_environment: Mapping[str, str] | None,
) -> list[dict[str, str]]:
    return [
        {"name": name, "value": str(value)}
        for name, value in sorted(dict(stack_environment or {}).items())
    ]


def _endpoint_mappings(payload: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(payload, Sequence) or isinstance(payload, str | bytes):
        return ()
    return tuple(endpoint for endpoint in payload if isinstance(endpoint, Mapping))


def _local_endpoint_fallback_id(
    endpoint_name: str,
    endpoints: tuple[Mapping[str, object], ...],
) -> int | None:
    if endpoint_name != "local":
        return None
    for endpoint in endpoints:
        name = str(endpoint.get("Name", "")).casefold()
        endpoint_id = _endpoint_id(endpoint)
        if name in {"primary", "docker", "swarm"} and endpoint_id is not None:
            return endpoint_id
    local_socket_endpoints = tuple(
        endpoint
        for endpoint in endpoints
        if "docker.sock" in str(endpoint.get("URL", "")).casefold()
    )
    if len(local_socket_endpoints) == 1:
        return _endpoint_id(local_socket_endpoints[0])
    return None


def _endpoint_id_by_name_or_local_fallback(
    endpoint_name: str,
    endpoints: tuple[Mapping[str, object], ...],
) -> int | None:
    for endpoint in endpoints:
        endpoint_id = _endpoint_id(endpoint)
        if endpoint.get("Name") == endpoint_name and endpoint_id is not None:
            return endpoint_id
    return _local_endpoint_fallback_id(endpoint_name, endpoints)


def _endpoint_id(endpoint: Mapping[str, object]) -> int | None:
    value = endpoint.get("Id")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    return None


def _available_endpoint_names(endpoints: tuple[Mapping[str, object], ...]) -> str:
    names = tuple(
        name
        for endpoint in endpoints
        if (name := str(endpoint.get("Name", "")).strip())
    )
    if not names:
        return "none"
    return ",".join(sorted(names))


def _extract_swarm_id(payload: object) -> str:
    if not isinstance(payload, Mapping):
        return ""
    swarm = payload.get("Swarm")
    if not isinstance(swarm, Mapping):
        return ""
    cluster = swarm.get("Cluster")
    if not isinstance(cluster, Mapping):
        return ""
    cluster_id = cluster.get("ID")
    if not isinstance(cluster_id, str):
        return ""
    return cluster_id
