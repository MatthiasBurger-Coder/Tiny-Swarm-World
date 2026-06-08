from __future__ import annotations

import io
import re
import shlex
import subprocess
import tarfile
from collections.abc import Mapping
from pathlib import Path

import requests
from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.clients.port_container_image_publisher import (
    PortContainerImagePublisher,
)
from tiny_swarm_world.application.ports.clients.port_container_runtime import (
    PortContainerRuntime,
)
from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.application.ports.clients.port_portainer_admin_client import (
    PortainerAdminInitializationRejected,
    PortPortainerAdminClient,
)
from tiny_swarm_world.application.ports.clients.port_portainer_client import (
    PortPortainerClient,
)
from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
    SwarmServiceStatus,
)
from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.domain.nexus.nexus_user import NexusUser
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import infra_root


REPLICA_PATTERN = re.compile(r"^(?P<current>\d+)/\s*(?P<desired>\d+)$")
STACK_ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
REMOTE_WORKDIR_PREFIX = "$PWD/"
_YAML = YAML(typ="safe")

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}


class LxcSwarmRuntime(PortSwarmStackRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        remote_stack_root: str = "/var/lib/tiny-swarm-world/stacks",
        timeout_seconds: int = 900,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Swarm runtime timeout must be positive.")
        self.backend = backend
        self.manager_node = manager_node
        self.remote_stack_root = remote_stack_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def prepare_stack_assets(self, stack_name: str) -> None:
        remote_dir = f"{self.remote_stack_root}/{stack_name}"
        self._transfer_stack_assets(stack_name, remote_dir)

    def deploy_stack(
        self,
        stack_definition: StackDefinition,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._ensure_stack_prerequisites(stack_definition.name, stack_definition)
        remote_dir = f"{self.remote_stack_root}/{stack_definition.name}"
        compose_path = f"{remote_dir}/docker-compose.yml"
        script = (
            f"set -e; mkdir -p {_quote_remote_path(remote_dir)}; "
            f"cat > {_quote_remote_path(compose_path)}"
        )
        self._run_manager_shell(script, input_text=stack_definition.compose_content)
        self.prepare_stack_assets(stack_definition.name)
        environment = {
            "TSW_REMOTE_STACK_ROOT": self.remote_stack_root,
            **dict(stack_environment or {}),
        }
        self._run_manager_shell(
            f"{_stack_environment_prefix(environment)} "
            f"docker stack deploy --detach=true -c {_quote_remote_path(compose_path)} "
            f"{shlex.quote(stack_definition.name)}"
        )
        self._reconcile_host_published_ports(stack_definition)

    def stack_exists(self, stack_name: str) -> bool:
        result = self._run_manager_shell(
            "docker stack ls --format '{{.Name}}'",
            check=False,
        )
        if result.returncode != 0:
            return False
        return stack_name in {line.strip() for line in result.stdout.splitlines()}

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        result = self._run_manager_shell(
            f"docker stack services --format '{{{{.Name}}}}|{{{{.Replicas}}}}' {shlex.quote(stack_name)}",
            check=False,
        )
        if result.returncode != 0:
            return ()
        return tuple(
            status
            for line in result.stdout.splitlines()
            if (status := _parse_service_status(line)) is not None
        )

    def external_secret_exists(self, name: str) -> bool:
        result = self._run_manager_shell(
            f"docker secret inspect -- {shlex.quote(name)} >/dev/null 2>&1",
            check=False,
        )
        return result.returncode == 0

    def ensure_external_secret(self, name: str, value: str) -> None:
        if self.external_secret_exists(name):
            return
        self._run_manager_shell(
            f"docker secret create -- {shlex.quote(name)} -",
            input_text=value,
        )

    def _ensure_stack_prerequisites(self, stack_name: str, stack_definition: StackDefinition) -> None:
        for network_name in _external_overlay_network_names(stack_definition):
            self._ensure_external_overlay_network(network_name)
        if stack_name != "sonarqube":
            return
        self._run_manager_shell(
            "sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null",
        )

    def _ensure_external_overlay_network(self, name: str) -> None:
        result = self._run_manager_shell(
            f"docker network inspect -- {shlex.quote(name)} >/dev/null 2>&1",
            check=False,
        )
        if result.returncode == 0:
            return
        self._run_manager_shell(
            "docker network create --driver overlay --attachable -- "
            f"{shlex.quote(name)} >/dev/null"
        )

    def _reconcile_host_published_ports(self, stack_definition: StackDefinition) -> None:
        for service_name, ports in _host_published_ports_by_service(stack_definition).items():
            swarm_service_name = f"{stack_definition.name}_{service_name}"
            for port in ports:
                published = str(port["published"])
                target = str(port["target"])
                protocol = str(port.get("protocol", "tcp"))
                current_mode = str(port.get("mode", "ingress"))
                desired_mode = str(port.get("resolved_mode", current_mode))
                self._run_manager_shell(
                    "docker service update "
                    f"--publish-rm published={shlex.quote(published)},"
                    f"target={shlex.quote(target)},"
                    f"protocol={shlex.quote(protocol)},"
                    f"mode={shlex.quote(current_mode)} "
                    f"{shlex.quote(swarm_service_name)} >/dev/null 2>&1 || true"
                )
                self._run_manager_shell(
                    "docker service update "
                    f"--publish-add published={shlex.quote(published)},"
                    f"target={shlex.quote(target)},"
                    f"protocol={shlex.quote(protocol)},mode={shlex.quote(desired_mode)} "
                    f"{shlex.quote(swarm_service_name)}"
                )

    def _transfer_stack_assets(self, stack_name: str, remote_dir: str) -> None:
        if stack_name != "swagger":
            return
        openapi_file = infra_root() / "compose" / "swagger" / "swagger" / "openapi.json"
        nginx_config = infra_root() / "compose" / "swagger" / "nginx" / "default.conf"
        script = (
            f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/swagger')}; "
            f"cat > {_quote_remote_path(remote_dir + '/swagger/openapi.json')}"
        )
        self._run_manager_shell(script, input_text=openapi_file.read_text(encoding="utf-8"))
        script = (
            f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/nginx')}; "
            f"cat > {_quote_remote_path(remote_dir + '/nginx/default.conf')}"
        )
        self._run_manager_shell(script, input_text=nginx_config.read_text(encoding="utf-8"))

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running LXC manager shell operation.")
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", self.manager_node, "--", "sh", "-lc", script],
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager Swarm operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(
                f"LXC manager Swarm operation failed with exit code {result.returncode}."
            )
        return result


class LxcContainerRuntime(PortContainerRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        timeout_seconds: int = 120,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Container runtime timeout must be positive.")
        self.backend = backend
        self.manager_node = manager_node
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def find_container_names(self, name_filter: str) -> list[str]:
        result = self._run_docker(
            ["ps", "--filter", f"name={name_filter}", "--format", "{{.Names}}"],
            check=False,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def file_exists(self, container_name: str, file_path: str) -> bool:
        result = self._run_docker(["exec", container_name, "test", "-f", file_path], check=False)
        return result.returncode == 0

    def read_file(self, container_name: str, file_path: str) -> str:
        result = self._run_docker(["exec", container_name, "cat", file_path], check=True)
        return result.stdout

    def _run_docker(
        self,
        docker_args: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        operation = docker_args[0] if docker_args else "operation"
        self.logger.info("Running LXC manager Docker operation '%s'.", operation)
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", self.manager_node, "--", "docker", *docker_args],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager Docker runtime operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(
                f"LXC manager Docker runtime operation failed with exit code {result.returncode}."
            )
        return result


class LxcPortainerAdminClient(PortPortainerAdminClient):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        port: int = 9000,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.backend = backend
        self.manager_node = manager_node
        self.port = port
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    def can_authenticate(self, username: str, password: str) -> bool:
        try:
            self._clear_session_cookies()
            response = self.session.post(
                f"{self._base_url()}/api/auth",
                json={"Username": username, "Password": password},
                timeout=self.timeout_seconds,
            )
            self._clear_session_cookies()
        except requests.RequestException:
            return False
        if response.status_code != 200:
            return False
        return bool(self._json_object(response).get("jwt"))

    def initialize_admin_user(self, username: str, password: str) -> None:
        try:
            self._clear_session_cookies()
            response = self.session.post(
                f"{self._base_url()}/api/users/admin/init",
                json={"username": username, "password": password},
                timeout=self.timeout_seconds,
            )
            self._clear_session_cookies()
        except requests.RequestException as exc:
            raise RuntimeError("Failed to initialize Portainer admin user.") from exc
        if response.status_code >= 400 and not self.can_authenticate(username, password):
            raise PortainerAdminInitializationRejected(
                f"Failed to initialize Portainer admin user. HTTP {response.status_code}.",
                status_code=response.status_code,
            )

    def _base_url(self) -> str:
        return f"http://{_lxc_manager_ip(self.backend, self.manager_node, self.timeout_seconds)}:{self.port}"

    def _clear_session_cookies(self) -> None:
        cookies = getattr(self.session, "cookies", None)
        clear = getattr(cookies, "clear", None)
        if callable(clear):
            clear()

    @staticmethod
    def _json_object(response: requests.Response) -> dict[str, object]:
        try:
            payload = response.json()
        except ValueError:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}


class LxcNexusHttpClient(PortNexusClient):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        port: int = 8081,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.backend = backend
        self.manager_node = manager_node
        self.port = port
        self.session = session
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        return self._client().is_available()

    def can_authenticate(self, username: str, password: str) -> bool:
        return self._client().can_authenticate(username, password)

    def get_user(self, username: str, password: str, target_user_id: str) -> NexusUser:
        return self._client().get_user(username, password, target_user_id)

    def update_user(self, username: str, password: str, user: NexusUser) -> None:
        self._client().update_user(username, password, user)

    def change_password(self, username: str, password: str, target_user_id: str, new_password: str) -> None:
        self._client().change_password(username, password, target_user_id, new_password)

    def set_anonymous_access(self, username: str, password: str, enabled: bool) -> None:
        self._client().set_anonymous_access(username, password, enabled)

    def repository_exists(self, username: str, password: str, repository_name: str) -> bool:
        return self._client().repository_exists(username, password, repository_name)

    def create_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self._client().create_docker_hosted_repository(
            username,
            password,
            repository_name,
            http_port,
        )

    def update_docker_hosted_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
    ) -> None:
        self._client().update_docker_hosted_repository(
            username,
            password,
            repository_name,
            http_port,
        )

    def create_maven_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        remote_url: str,
    ) -> None:
        self._client().create_maven_proxy_repository(username, password, repository_name, remote_url)

    def _client(self) -> NexusHttpClient:
        return NexusHttpClient(
            f"http://{_lxc_manager_ip(self.backend, self.manager_node, self.timeout_seconds)}:{self.port}",
            session=self.session,
        )


class LxcPortainerHttpClient(PortPortainerClient):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        username: str,
        password: str,
        manager_node: str = "swarm-manager",
        port: int = 9000,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.backend = backend
        self.username = username
        self.password = password
        self.manager_node = manager_node
        self.port = port
        self.session = session
        self.timeout_seconds = timeout_seconds

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        return self._client().get_endpoint_id_by_name(endpoint_name)

    def ensure_local_endpoint(self, endpoint_name: str) -> int:
        return self._client().ensure_local_endpoint(endpoint_name)

    def find_stack_id_by_name(self, stack_name: str) -> int | None:
        return self._client().find_stack_id_by_name(stack_name)

    def create_stack(
        self,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._ensure_external_overlay_networks(stack_definition)
        self._client().create_stack(stack_definition, endpoint_id, stack_environment)

    def update_stack(
        self,
        stack_id: int,
        stack_definition: StackDefinition,
        endpoint_id: int,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._ensure_external_overlay_networks(stack_definition)
        self._client().update_stack(
            stack_id,
            stack_definition,
            endpoint_id,
            stack_environment,
        )

    def _ensure_external_overlay_networks(self, stack_definition: StackDefinition) -> None:
        for network_name in _external_overlay_network_names(stack_definition):
            result = self._run_manager_shell(
                f"docker network inspect -- {shlex.quote(network_name)} >/dev/null 2>&1",
                check=False,
            )
            if result.returncode == 0:
                continue
            self._run_manager_shell(
                "docker network create --driver overlay --attachable -- "
                f"{shlex.quote(network_name)} >/dev/null"
            )

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", self.manager_node, "--", "sh", "-lc", script],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager Portainer prerequisite operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(
                f"LXC manager Portainer prerequisite operation failed with exit code {result.returncode}."
            )
        return result

    def _client(self) -> PortainerHttpClient:
        return PortainerHttpClient(
            f"http://{_lxc_manager_ip(self.backend, self.manager_node, self.timeout_seconds)}:{self.port}",
            self.username,
            self.password,
            session=self.session,
        )


class LxcContainerImagePublisher(PortContainerImagePublisher):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        registry_username: str,
        registry_password: str,
        manager_node: str = "swarm-manager",
        remote_image_root: str = "$PWD/.tiny-swarm-world/images",
        timeout_seconds: int = 1800,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Image publisher timeout must be positive.")
        self.backend = backend
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.manager_node = manager_node
        self.remote_image_root = remote_image_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def publish_image(self, contract: ContainerImageContract) -> None:
        context_path = self._context_path(contract)
        remote_context_path = f"{self.remote_image_root}/{contract.build_context}"
        self._transfer_context(context_path, remote_context_path)
        self._run_manager_shell(
            f"docker build -t {shlex.quote(contract.image_ref)} {_quote_remote_path(remote_context_path)}",
            timeout_seconds=self.timeout_seconds,
        )
        self._docker_login()
        self._run_manager_shell(
            f"docker push {shlex.quote(contract.image_ref)}",
            timeout_seconds=self.timeout_seconds,
        )

    def image_available(self, contract: ContainerImageContract) -> bool:
        self._docker_login()
        result = self._run_manager_shell(
            f"docker pull {shlex.quote(contract.image_ref)}",
            check=False,
            timeout_seconds=self.timeout_seconds,
        )
        return result.returncode == 0

    def _context_path(self, contract: ContainerImageContract) -> Path:
        contexts = {
            "jenkins": infra_root() / "compose" / "jenkins",
            "service-access-dashboard": infra_root() / "compose" / "service-access" / "dashboard",
            "service-access-nginx": infra_root() / "compose" / "service-access" / "nginx",
        }
        try:
            return contexts[contract.build_context]
        except KeyError as exc:
            raise ValueError(f"Unknown image build context '{contract.build_context}'.") from exc

    def _transfer_context(self, context_path: Path, remote_context_path: str) -> None:
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            for source_file in sorted(context_path.iterdir()):
                if source_file.is_file():
                    tar.add(source_file, arcname=source_file.name)
        archive.seek(0)
        self._run_manager_shell_bytes(
            f"set -e; mkdir -p {_quote_remote_path(remote_context_path)}; "
            f"tar -x -C {_quote_remote_path(remote_context_path)}",
            input_bytes=archive.getvalue(),
            timeout_seconds=self.timeout_seconds,
        )

    def _docker_login(self) -> None:
        self._run_manager_shell(
            f"docker login -u {shlex.quote(self.registry_username)} --password-stdin 127.0.0.1:5000",
            input_text=f"{self.registry_password}\n",
            timeout_seconds=120,
        )

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running LXC manager image operation.")
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", self.manager_node, "--", "sh", "-lc", script],
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager image operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(
                f"LXC manager image operation failed with exit code {result.returncode}."
            )
        return result

    def _run_manager_shell_bytes(
        self,
        script: str,
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[bytes]:
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", self.manager_node, "--", "sh", "-lc", script],
                input=input_bytes,
                capture_output=True,
                check=False,
                shell=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LXC manager image transfer timed out.") from exc
        if result.returncode != 0:
            raise RuntimeError(
                f"LXC manager image transfer failed with exit code {result.returncode}."
            )
        return result


def _lxc_manager_ip(
    backend: ManagedLxcBackend,
    manager_node: str,
    timeout_seconds: int,
) -> str:
    try:
        result = subprocess.run(
            [
                _BACKEND_CLI[backend],
                "exec",
                manager_node,
                "--",
                "sh",
                "-lc",
                "ip -4 -o addr show dev eth0 | awk '{print $4}' | cut -d/ -f1",
            ],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("LXC manager IP lookup timed out.") from exc
    if result.returncode != 0:
        raise RuntimeError("LXC manager IP lookup failed.")
    addresses = [part for part in result.stdout.split() if "." in part]
    if not addresses:
        raise RuntimeError("LXC manager IP lookup returned no IPv4 address.")
    return addresses[0]


def _parse_service_status(line: str) -> SwarmServiceStatus | None:
    if "|" not in line:
        return None
    service_name, replicas = (part.strip() for part in line.split("|", 1))
    match = REPLICA_PATTERN.fullmatch(replicas)
    if match is None:
        return None
    return SwarmServiceStatus(
        service_name=service_name,
        current_replicas=int(match.group("current")),
        desired_replicas=int(match.group("desired")),
    )


def _host_published_ports_by_service(
    stack_definition: StackDefinition,
) -> dict[str, tuple[Mapping[str, object], ...]]:
    payload = _YAML.load(stack_definition.compose_content) or {}
    if not isinstance(payload, Mapping):
        return {}
    services = payload.get("services", {})
    if not isinstance(services, Mapping):
        return {}

    selected: dict[str, tuple[Mapping[str, object], ...]] = {}
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str) or not isinstance(service_payload, Mapping):
            continue
        ports = service_payload.get("ports", ())
        if not isinstance(ports, list):
            continue
        manager_only = _service_is_manager_constrained(service_payload)
        host_ports = tuple(
            {
                **dict(port),
                "resolved_mode": "host" if manager_only else "ingress",
            }
            for port in ports
            if (
                isinstance(port, Mapping)
                and port.get("mode") == "host"
                and "published" in port
                and "target" in port
            )
        )
        if host_ports:
            selected[service_name] = host_ports
    return selected


def _external_overlay_network_names(stack_definition: StackDefinition) -> tuple[str, ...]:
    payload = _YAML.load(stack_definition.compose_content) or {}
    if not isinstance(payload, Mapping):
        return ()
    networks = payload.get("networks", {})
    if not isinstance(networks, Mapping):
        return ()

    names: list[str] = []
    for fallback_name, network_payload in networks.items():
        if not isinstance(fallback_name, str) or not isinstance(network_payload, Mapping):
            continue
        if network_payload.get("external") is not True:
            continue
        configured_name = network_payload.get("name", fallback_name)
        if isinstance(configured_name, str) and configured_name.strip():
            names.append(configured_name.strip())
    return tuple(dict.fromkeys(names))


def _service_is_manager_constrained(service_payload: Mapping[str, object]) -> bool:
    deploy = service_payload.get("deploy", {})
    if not isinstance(deploy, Mapping):
        return False
    placement = deploy.get("placement", {})
    if not isinstance(placement, Mapping):
        return False
    constraints = placement.get("constraints", ())
    if isinstance(constraints, str) or not isinstance(constraints, list):
        return False
    normalized = {str(constraint).replace(" ", "").casefold() for constraint in constraints}
    return "node.role==manager" in normalized


def _stack_environment_prefix(environment: Mapping[str, str]) -> str:
    assignments: list[str] = []
    for name, value in sorted(environment.items()):
        if not STACK_ENVIRONMENT_NAME_PATTERN.fullmatch(name):
            raise ValueError("Stack environment name contains invalid characters.")
        assignments.append(f"{name}={_quote_remote_path(str(value))}")
    return " ".join(assignments)


def _quote_remote_path(path: str) -> str:
    if path.startswith(REMOTE_WORKDIR_PREFIX):
        return f"{REMOTE_WORKDIR_PREFIX}{shlex.quote(path.removeprefix(REMOTE_WORKDIR_PREFIX))}"
    return shlex.quote(path)
