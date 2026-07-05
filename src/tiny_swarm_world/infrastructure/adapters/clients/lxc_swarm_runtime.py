from __future__ import annotations

import io
import json
import re
import shlex
import subprocess
import tarfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path

import requests
from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.clients.port_container_image_publisher import (
    PortContainerImagePublisher,
)
from tiny_swarm_world.application.ports.clients.port_container_runtime import (
    PortContainerRuntime,
)
from tiny_swarm_world.application.ports.clients.port_deployment_gateway import (
    DeploymentStackRequest,
    PortDeploymentGateway,
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
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths


REPLICA_PATTERN = re.compile(r"^(?P<current>\d+)/\s*(?P<desired>\d+)$")
STACK_ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
REMOTE_WORKDIR_PREFIX = "$PWD/"
_YAML = YAML(typ="safe")

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_MANAGER_SHELL_MAX_ATTEMPTS = 3
_MANAGER_SHELL_RETRY_DELAYS_SECONDS = (0.5, 1.0)
_INCUS_CHILD_PID_FAILURE = "Failed to retrieve PID of executing child process"


class LxcSwarmRuntime(PortSwarmStackRuntime):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        remote_stack_root: str = "/var/lib/tiny-swarm-world/stacks",
        timeout_seconds: int = 900,
        service_list_timeout_seconds: int = 30,
        project_paths: ProjectPaths | None = None,
        service_access_dashboard_renderer: Callable[[], str] | None = None,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Swarm runtime timeout must be positive.")
        if service_list_timeout_seconds <= 0:
            raise ValueError("Swarm service list timeout must be positive.")
        self.backend = backend
        self.manager_node = manager_node
        self.remote_stack_root = remote_stack_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.service_list_timeout_seconds = service_list_timeout_seconds
        self.project_paths = project_paths or default_project_paths()
        self.service_access_dashboard_renderer = service_access_dashboard_renderer
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
            f"docker stack deploy --detach=true --resolve-image never "
            "--with-registry-auth "
            f"-c {_quote_remote_path(compose_path)} "
            f"{shlex.quote(stack_definition.name)}"
        )

    def stack_exists(self, stack_name: str) -> bool:
        result = self._run_manager_shell(
            "docker stack ls --format '{{.Name}}'",
            check=False,
        )
        if result.returncode != 0:
            return False
        return stack_name in {line.strip() for line in result.stdout.splitlines()}

    def list_stack_services(self, stack_name: str) -> tuple[SwarmServiceStatus, ...]:
        remote_timeout = shlex.quote(f"{self.service_list_timeout_seconds}s")
        stack_filter = shlex.quote(f"label=com.docker.stack.namespace={stack_name}")
        result = self._run_manager_shell(
            "timeout --kill-after=5s "
            f"{remote_timeout} docker service ls --filter {stack_filter} "
            "--format '{{.Name}}|{{.Replicas}}'",
            check=False,
            timeout_seconds=self.service_list_timeout_seconds + 10,
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

    def recover_infisical_migration_lock(self) -> bool:
        script = (
            "set -e; "
            "db_container=$(docker ps --filter name=infisical-db "
            "--format '{{.Names}}' | head -n 1); "
            "test -n \"$db_container\"; "
            "for lock_table in infisical_migrations_lock infisical_migrations_startup_lock; do "
            "if docker exec \"$db_container\" psql -U infisical -d infisical -tAc "
            "\"select to_regclass('public.' || '$lock_table')\" | grep -q \"$lock_table\"; then "
            "docker exec \"$db_container\" psql -U infisical -d infisical -c "
            "\"update $lock_table set is_locked=0 where is_locked<>0\" >/dev/null; "
            "fi; "
            "done"
        )
        result = self._run_manager_shell(script, check=False)
        return result.returncode == 0

    def _ensure_stack_prerequisites(self, stack_name: str, stack_definition: StackDefinition) -> None:
        for network_name in _external_overlay_network_names(stack_definition):
            self._ensure_external_overlay_network(network_name)
        if stack_name == "traefik":
            self._ensure_traefik_tls_secrets()
        if stack_name != "sonarqube":
            return
        self._run_manager_shell(
            "sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null",
        )

    def _ensure_traefik_tls_secrets(self) -> None:
        cert_secret = "tsw_traefik_tls_cert"
        key_secret = "tsw_traefik_tls_key"
        if self.external_secret_exists(cert_secret) and self.external_secret_exists(key_secret):
            return
        script = (
            "set -e; "
            "tmpdir=$(mktemp -d); "
            "trap 'rm -rf \"$tmpdir\"' EXIT; "
            "openssl req -x509 -nodes -newkey rsa:2048 -days 365 "
            "-subj '/CN=tsw.local' "
            "-addext 'subjectAltName=DNS:tsw.local,DNS:*.tsw.local,DNS:localhost' "
            "-keyout \"$tmpdir/tls.key\" -out \"$tmpdir/tls.crt\" >/dev/null 2>&1; "
            f"docker secret inspect -- {shlex.quote(cert_secret)} >/dev/null 2>&1 "
            f"|| docker secret create -- {shlex.quote(cert_secret)} \"$tmpdir/tls.crt\" >/dev/null; "
            f"docker secret inspect -- {shlex.quote(key_secret)} >/dev/null 2>&1 "
            f"|| docker secret create -- {shlex.quote(key_secret)} \"$tmpdir/tls.key\" >/dev/null"
        )
        self._run_manager_shell(script)

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
            existing_ports = self._published_ports(swarm_service_name)
            publish_removes = tuple(
                _publish_rm_argument_from_key(existing_port)
                for port in ports
                for existing_port in _matching_published_ports(existing_ports, port)
                if existing_port != _published_port_key(port)
            )
            publish_adds = tuple(
                _publish_add_argument(port)
                for port in ports
                if _published_port_key(port) not in existing_ports
            )
            if not publish_removes and not publish_adds:
                continue
            self._run_manager_shell(
                "docker service update "
                + " ".join(f"--publish-rm {publish_remove}" for publish_remove in publish_removes)
                + (" " if publish_removes and publish_adds else "")
                + " ".join(f"--publish-add {publish_add}" for publish_add in publish_adds)
                + f" {shlex.quote(swarm_service_name)}"
            )

    def _published_ports(self, swarm_service_name: str) -> set[tuple[str, str, str, str]]:
        result = self._run_manager_shell(
            "docker service inspect "
            f"{shlex.quote(swarm_service_name)} "
            "--format '{{json .Spec.EndpointSpec.Ports}}'",
            check=False,
        )
        if result.returncode != 0:
            return set()
        return _published_ports_from_json(result.stdout)

    def _transfer_stack_assets(self, stack_name: str, remote_dir: str) -> None:
        if stack_name == "traefik":
            tls_config = (
                self.project_paths.infra_root
                / "config"
                / "compose"
                / "traefik"
                / "dynamic"
                / "tls.yml"
            )
            script = (
                f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/dynamic')}; "
                f"cat > {_quote_remote_path(remote_dir + '/dynamic/tls.yml')}"
            )
            self._run_manager_shell(script, input_text=tls_config.read_text(encoding="utf-8"))
            return
        if stack_name == "service-access":
            script = (
                f"set -e; mkdir -p {_quote_remote_path(remote_dir + '/dashboard')}; "
                f"cat > {_quote_remote_path(remote_dir + '/dashboard/index.html')}"
            )
            self._run_manager_shell(script, input_text=self._render_service_access_dashboard())
            return
        if stack_name != "swagger":
            return
        openapi_file = (
            self.project_paths.infra_root
            / "config"
            / "compose"
            / "swagger"
            / "swagger"
            / "openapi.json"
        )
        nginx_config = (
            self.project_paths.infra_root
            / "config"
            / "compose"
            / "swagger"
            / "nginx"
            / "default.conf"
        )
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

    def _render_service_access_dashboard(self) -> str:
        if self.service_access_dashboard_renderer is not None:
            return self.service_access_dashboard_renderer()
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
            ComposeFileRepositoryYaml,
        )

        return ComposeFileRepositoryYaml(
            project_paths=self.project_paths,
        ).render_service_access_dashboard()

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        timeout_seconds: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running LXC manager shell operation script=%s", _safe_log_text(script))
        timeout = timeout_seconds or self.timeout_seconds
        result: subprocess.CompletedProcess[str] | None = None
        for attempt in range(1, _MANAGER_SHELL_MAX_ATTEMPTS + 1):
            try:
                result = subprocess.run(
                    [_BACKEND_CLI[self.backend], "exec", self.manager_node, "--", "sh", "-lc", script],
                    input=input_text,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=False,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("LXC manager Swarm operation timed out.") from exc
            log = self.logger.warning if result.returncode != 0 else self.logger.info
            log(
                "lxc_swarm_runtime manager_shell_result returncode=%s stdout=%s stderr=%s",
                result.returncode,
                _safe_log_text(result.stdout),
                _safe_log_text(result.stderr),
            )
            if not _is_transient_manager_shell_failure(result):
                break
            if attempt >= _MANAGER_SHELL_MAX_ATTEMPTS:
                break
            delay_seconds = _MANAGER_SHELL_RETRY_DELAYS_SECONDS[
                min(attempt - 1, len(_MANAGER_SHELL_RETRY_DELAYS_SECONDS) - 1)
            ]
            self.logger.warning(
                "Retrying transient LXC manager shell operation after Incus child PID failure "
                "attempt=%s next_attempt=%s delay_seconds=%s",
                attempt,
                attempt + 1,
                delay_seconds,
            )
            time.sleep(delay_seconds)
        if result is None:
            raise RuntimeError("LXC manager Swarm operation did not execute.")
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
        node_names: tuple[str, ...] = ("swarm-manager",),
        timeout_seconds: int = 120,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Container runtime timeout must be positive.")
        if not node_names:
            raise ValueError("Container runtime node list must not be empty.")
        self.backend = backend
        self.manager_node = manager_node
        self.node_names = tuple(dict.fromkeys(node_names))
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def find_container_names(self, name_filter: str) -> list[str]:
        container_names: list[str] = []
        for node_name in self.node_names:
            result = self._run_docker(
                ["ps", "--filter", f"name={name_filter}", "--format", "{{.Names}}"],
                check=False,
                node_name=node_name,
            )
            container_names.extend(
                _lxc_container_ref(node_name, line.strip())
                for line in result.stdout.splitlines()
                if line.strip()
            )
        return container_names

    def file_exists(self, container_name: str, file_path: str) -> bool:
        node_name, resolved_container_name = _split_lxc_container_ref(
            container_name,
            self.manager_node,
        )
        result = self._run_docker(
            ["exec", resolved_container_name, "test", "-f", file_path],
            check=False,
            node_name=node_name,
        )
        return result.returncode == 0

    def read_file(self, container_name: str, file_path: str) -> str:
        node_name, resolved_container_name = _split_lxc_container_ref(
            container_name,
            self.manager_node,
        )
        result = self._run_docker(
            ["exec", resolved_container_name, "cat", file_path],
            check=True,
            node_name=node_name,
        )
        return result.stdout

    def _run_docker(
        self,
        docker_args: list[str],
        *,
        check: bool,
        node_name: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        operation = docker_args[0] if docker_args else "operation"
        target_node = node_name or self.manager_node
        self.logger.info("Running LXC Docker operation '%s' on node '%s'.", operation, target_node)
        try:
            result = subprocess.run(
                [_BACKEND_CLI[self.backend], "exec", target_node, "--", "docker", *docker_args],
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


def _lxc_container_ref(node_name: str, container_name: str) -> str:
    return f"{node_name}::{container_name}"


def _split_lxc_container_ref(container_ref: str, default_node: str) -> tuple[str, str]:
    node_name, separator, container_name = container_ref.partition("::")
    if not separator:
        return default_node, container_ref
    return node_name, container_name


class LxcPortainerAdminClient(PortPortainerAdminClient):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str = "swarm-manager",
        port: int = 10001,
        scheme: str = "http",
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.backend = backend
        self.manager_node = manager_node
        self.port = port
        self.scheme = _validate_local_http_scheme(scheme)
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
        return _local_service_url(
            self.scheme,
            _lxc_manager_ip(self.backend, self.manager_node, self.timeout_seconds),
            self.port,
        )

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
        port: int = 13081,
        scheme: str = "http",
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ):
        self.backend = backend
        self.manager_node = manager_node
        self.port = port
        self.scheme = _validate_local_http_scheme(scheme)
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

    def create_docker_proxy_repository(
        self,
        username: str,
        password: str,
        repository_name: str,
        http_port: int,
        remote_url: str,
    ) -> None:
        self._client().create_docker_proxy_repository(
            username,
            password,
            repository_name,
            http_port,
            remote_url,
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
            self._base_url(),
            session=self.session,
        )

    def _base_url(self) -> str:
        return _local_service_url(
            self.scheme,
            _lxc_manager_ip(self.backend, self.manager_node, self.timeout_seconds),
            self.port,
        )


class LxcPortainerHttpClient(PortPortainerClient, PortDeploymentGateway):
    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        username: str,
        password: str,
        manager_node: str = "swarm-manager",
        port: int = 10001,
        scheme: str = "http",
        api_url: str | None = None,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
        stack_request_timeout_seconds: int = 180,
    ):
        if stack_request_timeout_seconds <= 0:
            raise ValueError("Portainer stack request timeout must be positive.")
        self.backend = backend
        self.username = username
        self.password = password
        self.manager_node = manager_node
        self.port = port
        self.scheme = _validate_local_http_scheme(scheme)
        self.api_url = api_url.rstrip("/") if api_url else None
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.stack_request_timeout_seconds = stack_request_timeout_seconds
        self._cached_client: PortainerHttpClient | None = None

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

    def apply_stack(self, request: DeploymentStackRequest) -> None:
        endpoint_id = self.get_endpoint_id_by_name("local")
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
        if self._cached_client is None:
            self._cached_client = PortainerHttpClient(
                self.api_url or self._base_url(),
                self.username,
                self.password,
                session=self.session,
                request_timeout_seconds=self.timeout_seconds,
                stack_request_timeout_seconds=self.stack_request_timeout_seconds,
            )
        return self._cached_client

    def _base_url(self) -> str:
        return _local_service_url(
            self.scheme,
            _lxc_manager_ip(self.backend, self.manager_node, self.timeout_seconds),
            self.port,
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
        project_paths: ProjectPaths | None = None,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Image publisher timeout must be positive.")
        self.backend = backend
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.manager_node = manager_node
        self.remote_image_root = remote_image_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.project_paths = project_paths or default_project_paths()
        self.logger = LoggerFactory.get_logger(self.__class__)

    def publish_image(self, contract: ContainerImageContract) -> None:
        if contract.source == "pull":
            self._pull_public_image(contract)
            return
        context_path = self._context_path(contract)
        remote_context_path = f"{self.remote_image_root}/{contract.build_context}"
        self._transfer_context(context_path, remote_context_path)
        build_script = (
            f"docker build -t {shlex.quote(contract.image_ref)} "
            f"{_quote_remote_path(remote_context_path)}"
        )
        self._run_manager_shell(
            build_script,
            operation="build_image",
            timeout_seconds=self.timeout_seconds,
        )
        self._docker_login()
        self._run_manager_shell(
            f"docker push {shlex.quote(contract.image_ref)}",
            operation="push_image",
            timeout_seconds=self.timeout_seconds,
        )

    def image_available(self, contract: ContainerImageContract) -> bool:
        if contract.source == "build":
            self._docker_login()
        elif self._load_host_cached_image(contract):
            return True
        result = self._run_manager_shell(
            f"docker pull {shlex.quote(contract.image_ref)}",
            check=False,
            operation="verify_image_pull",
            timeout_seconds=self.timeout_seconds,
        )
        if result.returncode != 0 and _docker_hub_rate_limited(result):
            if self._load_host_cached_image(contract):
                return True
            raise PublicImagePullRejected(
                contract.image_ref,
                diagnostic="registry_rate_limited",
                operator_action=(
                    "Configure Docker Hub authentication, an approved registry mirror, "
                    "or a provider-managed image cache."
                ),
            )
        return result.returncode == 0

    def _pull_public_image(self, contract: ContainerImageContract) -> None:
        if self._load_host_cached_image(contract):
            return
        result = self._run_manager_shell(
            f"docker pull {shlex.quote(contract.image_ref)}",
            check=False,
            operation="pull_public_image",
            timeout_seconds=self.timeout_seconds,
        )
        if result.returncode == 0:
            return
        if _docker_hub_rate_limited(result):
            if self._load_host_cached_image(contract):
                return
            raise PublicImagePullRejected(
                contract.image_ref,
                diagnostic="registry_rate_limited",
                operator_action=(
                    "Configure Docker Hub authentication, an approved registry mirror, "
                    "or a provider-managed image cache."
                ),
            )
        raise RuntimeError("Public container image pull failed.")

    def _load_host_cached_image(self, contract: ContainerImageContract) -> bool:
        try:
            inspect_result = subprocess.run(
                ["docker", "image", "inspect", contract.image_ref],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=120,
            )
        except FileNotFoundError:
            return False
        if inspect_result.returncode != 0:
            return False

        command = (
            "set -o pipefail; "
            f"docker save {shlex.quote(contract.image_ref)} | "
            f"{shlex.quote(_BACKEND_CLI[self.backend])} exec {shlex.quote(self.manager_node)} -- docker load"
        )
        load_result = subprocess.run(
            ["bash", "-lc", command],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=self.timeout_seconds,
        )
        return load_result.returncode == 0

    def _context_path(self, contract: ContainerImageContract) -> Path:
        contexts = {
            "jenkins": self.project_paths.infra_root / "config" / "compose" / "jenkins" / "image",
            "service-access-dashboard": self.project_paths.infra_root / "config" / "compose" / "service-access" / "dashboard",
            "service-access-nginx": self.project_paths.infra_root / "config" / "compose" / "service-access" / "nginx",
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
        login_script = (
            f"docker login -u {shlex.quote(self.registry_username)} "
            "--password-stdin 127.0.0.1:13500"
        )
        self._run_manager_shell(
            login_script,
            input_text=f"{self.registry_password}\n",
            operation="registry_login",
            timeout_seconds=120,
        )

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        operation: str = "manager_image_operation",
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
            raise ImagePublisherOperationRejected(
                operation=operation,
                diagnostic="operation_timeout",
                operator_action=(
                    "Inspect the manager node Docker daemon and retry the artifact prepare phase."
                ),
            ) from exc
        if check and result.returncode != 0:
            raise ImagePublisherOperationRejected(
                operation=operation,
                diagnostic=_image_operation_failure_diagnostic(operation, result),
                operator_action=_image_operation_operator_action(operation, result),
                exit_code=result.returncode,
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


class PublicImagePullRejected(RuntimeError):
    def __init__(self, image_ref: str, *, diagnostic: str, operator_action: str):
        super().__init__(f"Public container image pull failed for {image_ref}.")
        self.image_ref = image_ref
        self.diagnostic = diagnostic
        self.operator_action = operator_action


class ImagePublisherOperationRejected(RuntimeError):
    def __init__(
        self,
        *,
        operation: str,
        diagnostic: str,
        operator_action: str,
        exit_code: int | None = None,
    ):
        message = f"Container image publisher operation failed: {operation}."
        if exit_code is not None:
            message = f"{message} Exit code: {exit_code}."
        super().__init__(message)
        self.operation = operation
        self.diagnostic = diagnostic
        self.operator_action = operator_action
        self.exit_code = exit_code


def _docker_hub_rate_limited(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stdout}\n{result.stderr}".lower()
    return "pull rate limit" in output or "too many requests" in output


def _image_operation_failure_diagnostic(
    operation: str,
    result: subprocess.CompletedProcess[str],
) -> str:
    output = f"{result.stdout}\n{result.stderr}".lower()
    if _docker_hub_rate_limited(result):
        return "registry_rate_limited"
    if "connection refused" in output or "no route to host" in output:
        if operation in {"registry_login", "push_image"}:
            return "registry_unreachable"
        return "network_unreachable"
    if "unauthorized" in output or "authentication required" in output:
        return "registry_authentication_failed"
    if "no space left on device" in output:
        return "manager_storage_exhausted"
    if operation == "build_image":
        return "image_build_failed"
    if operation == "push_image":
        return "registry_push_failed"
    if operation == "registry_login":
        return "registry_login_failed"
    return "manager_image_operation_failed"


def _image_operation_operator_action(
    operation: str,
    result: subprocess.CompletedProcess[str],
) -> str:
    diagnostic = _image_operation_failure_diagnostic(operation, result)
    if diagnostic == "registry_rate_limited":
        return (
            "Configure Docker Hub authentication, an approved registry mirror, "
            "or a provider-managed image cache."
        )
    if diagnostic == "registry_unreachable":
        return (
            "Verify that the Nexus Docker hosted registry is reachable from the "
            "manager node at 127.0.0.1:13500."
        )
    if diagnostic == "registry_authentication_failed":
        return "Verify TSW_NEXUS_ADMIN_PASSWORD and Nexus Docker hosted repository access."
    if diagnostic == "manager_storage_exhausted":
        return "Free storage on the manager node before rerunning artifacts prepare."
    if operation == "build_image":
        return (
            "Inspect the manager node Docker build prerequisites and the transferred "
            "image context."
        )
    if operation == "push_image":
        return (
            "Verify the local registry service, repository port, and manager-node "
            "registry trust."
        )
    return "Inspect the manager node Docker daemon and rerun artifacts prepare."


def _lxc_manager_ip(
    backend: ManagedLxcBackend,
    manager_node: str,
    timeout_seconds: int,
) -> str:
    result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, _MANAGER_SHELL_MAX_ATTEMPTS + 1):
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
        if not _is_transient_manager_shell_failure(result):
            break
        if attempt >= _MANAGER_SHELL_MAX_ATTEMPTS:
            break
        delay_seconds = _MANAGER_SHELL_RETRY_DELAYS_SECONDS[
            min(attempt - 1, len(_MANAGER_SHELL_RETRY_DELAYS_SECONDS) - 1)
        ]
        time.sleep(delay_seconds)
    if result is None:
        raise RuntimeError("LXC manager IP lookup did not execute.")
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
        host_ports = tuple(
            {
                **dict(port),
                "resolved_mode": "host",
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


def _publish_add_argument(port: Mapping[str, object]) -> str:
    published = str(port["published"])
    target = str(port["target"])
    protocol = str(port.get("protocol", "tcp"))
    current_mode = str(port.get("mode", "ingress"))
    desired_mode = str(port.get("resolved_mode", current_mode))
    return (
        f"published={shlex.quote(published)},"
        f"target={shlex.quote(target)},"
        f"protocol={shlex.quote(protocol)},"
        f"mode={shlex.quote(desired_mode)}"
    )


def _validate_local_http_scheme(scheme: str) -> str:
    normalized = scheme.strip().lower()
    if normalized not in {"http", "https"}:
        raise ValueError("Local service URL scheme must be 'http' or 'https'.")
    return normalized


def _local_service_url(scheme: str, host: str, port: int) -> str:
    return f"{scheme}://{host}:{port}"


def _published_port_key(port: Mapping[str, object]) -> tuple[str, str, str, str]:
    current_mode = str(port.get("mode", "ingress"))
    return (
        str(port["published"]),
        str(port["target"]),
        str(port.get("protocol", "tcp")),
        str(port.get("resolved_mode", current_mode)),
    )


def _matching_published_ports(
    existing_ports: set[tuple[str, str, str, str]],
    port: Mapping[str, object],
) -> tuple[tuple[str, str, str, str], ...]:
    published = str(port["published"])
    target = str(port["target"])
    protocol = str(port.get("protocol", "tcp"))
    return tuple(
        existing_port
        for existing_port in existing_ports
        if existing_port[:3] == (published, target, protocol)
    )


def _publish_rm_argument_from_key(port: tuple[str, str, str, str]) -> str:
    published, target, protocol, mode = port
    return (
        f"published={shlex.quote(published)},"
        f"target={shlex.quote(target)},"
        f"protocol={shlex.quote(protocol)},"
        f"mode={shlex.quote(mode)}"
    )


def _published_ports_from_json(value: str) -> set[tuple[str, str, str, str]]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return set()
    if not isinstance(payload, list):
        return set()
    ports: set[tuple[str, str, str, str]] = set()
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        published = item.get("PublishedPort")
        target = item.get("TargetPort")
        protocol = item.get("Protocol", "tcp")
        mode = item.get("PublishMode", "ingress")
        if published is None or target is None:
            continue
        ports.add((str(published), str(target), str(protocol), str(mode)))
    return ports


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


_SENSITIVE_LOG_ASSIGNMENT_PATTERN = re.compile(
    r"\b([A-Za-z0-9_]*(?:PASSWORD|TOKEN|SECRET|KEY)[A-Za-z0-9_]*)="
    r"(?:'[^']*'|\"[^\"]*\"|\S+)",
    re.IGNORECASE,
)
_SENSITIVE_BEARER_PATTERN = re.compile(
    r"(authorization:\s*bearer\s+)\S+",
    re.IGNORECASE,
)
_SENSITIVE_TOKEN_PARAMETER_PATTERN = re.compile(
    r"\b(token:)[^\s'\"]+",
    re.IGNORECASE,
)


def _is_transient_manager_shell_failure(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode == 255 and _INCUS_CHILD_PID_FAILURE in result.stderr


def _safe_log_text(value: str, limit: int = 500) -> str:
    collapsed = " ".join(value.split())
    collapsed = _SENSITIVE_LOG_ASSIGNMENT_PATTERN.sub(r"\1=***", collapsed)
    collapsed = _SENSITIVE_BEARER_PATTERN.sub(r"\1***", collapsed)
    collapsed = _SENSITIVE_TOKEN_PARAMETER_PATTERN.sub(r"\1***", collapsed)
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}..."
