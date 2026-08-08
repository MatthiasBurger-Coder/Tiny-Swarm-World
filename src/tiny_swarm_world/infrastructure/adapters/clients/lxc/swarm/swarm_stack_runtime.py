"""Swarm stack behavior extracted from the legacy LXC runtime adapter."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
from collections.abc import Callable, Mapping

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    SwarmServiceStatus,
)
from tiny_swarm_world.domain.deployment import StackDefinition


REPLICA_PATTERN = re.compile(r"^(?P<current>\d+)/\s*(?P<desired>\d+)$")
STACK_ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
REMOTE_WORKDIR_PREFIX = "$PWD/"
_YAML = YAML(typ="safe")

ManagerShell = Callable[..., subprocess.CompletedProcess[str]]
NodeShell = Callable[..., subprocess.CompletedProcess[str]]
StackAssetPreparer = Callable[[str, str], None]
StackPrerequisiteEnsurer = Callable[[str, StackDefinition], None]


class LxcSwarmStackRuntime:
    """Coordinate Swarm stack operations through injected infrastructure seams."""

    def __init__(
        self,
        *,
        remote_stack_root: str,
        service_list_timeout_seconds: int,
        run_manager_shell: ManagerShell,
        run_node_shell: NodeShell,
        prepare_stack_assets: StackAssetPreparer,
        ensure_stack_prerequisites: StackPrerequisiteEnsurer,
        external_secret_exists: Callable[[str], bool] | None = None,
    ) -> None:
        self.remote_stack_root = remote_stack_root.rstrip("/")
        self.service_list_timeout_seconds = service_list_timeout_seconds
        self._run_manager_shell = run_manager_shell
        self._run_node_shell = run_node_shell
        self._prepare_stack_assets = prepare_stack_assets
        self._ensure_stack_prerequisites = ensure_stack_prerequisites
        self._external_secret_exists = external_secret_exists or self.external_secret_exists

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
        self._prepare_stack_assets(stack_definition.name, remote_dir)
        environment = {
            "TSW_REMOTE_STACK_ROOT": self.remote_stack_root,
            **dict(stack_environment or {}),
        }
        self._run_manager_shell(
            f"{_stack_environment_prefix(environment)} "
            "docker stack deploy --detach=true --resolve-image never "
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
        if self._external_secret_exists(name):
            return
        self._run_manager_shell(
            f"docker secret create -- {shlex.quote(name)} -",
            input_text=value,
        )

    def recover_infisical_migration_lock(self) -> bool:
        database_service = shlex.quote("infisical_infisical-db")
        placement = self._run_manager_shell(
            "docker service ps --filter desired-state=running "
            f"--format '{{{{.Node}}}}' {database_service}",
            check=False,
        )
        if placement.returncode != 0:
            return False
        task_nodes = tuple(
            dict.fromkeys(
                line.strip()
                for line in (placement.stdout or "").splitlines()
                if line.strip()
            )
        )
        if len(task_nodes) != 1:
            return False
        script = (
            "set -e; "
            "db_containers=$(docker ps "
            "--filter "
            f"label=com.docker.swarm.service.name={database_service} "
            "--format '{{.Names}}'); "
            "test \"$(printf '%s\\n' \"$db_containers\" | sed '/^$/d' | wc -l)\" -eq 1; "
            "db_container=$(printf '%s\\n' \"$db_containers\" | sed '/^$/d'); "
            "for lock_table in infisical_migrations_lock infisical_migrations_startup_lock; do "
            "if docker exec \"$db_container\" psql -U infisical -d infisical -tAc "
            "\"select to_regclass('public.' || '$lock_table')\" | grep -q \"$lock_table\"; then "
            "docker exec \"$db_container\" psql -U infisical -d infisical -c "
            "\"update $lock_table set is_locked=0 where is_locked<>0\" >/dev/null; "
            "fi; "
            "done"
        )
        result = self._run_node_shell(task_nodes[0], script, check=False)
        return result.returncode == 0

    def reconcile_host_published_ports(self, stack_definition: StackDefinition) -> None:
        for service_name, ports in _host_published_ports_by_service(stack_definition).items():
            swarm_service_name = f"{stack_definition.name}_{service_name}"
            existing_ports = self.published_ports(swarm_service_name)
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

    def published_ports(self, swarm_service_name: str) -> set[tuple[str, str, str, str]]:
        result = self._run_manager_shell(
            "docker service inspect "
            f"{shlex.quote(swarm_service_name)} "
            "--format '{{json .Spec.EndpointSpec.Ports}}'",
            check=False,
        )
        if result.returncode != 0:
            return set()
        return _published_ports_from_json(result.stdout)


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
    for network_key, network_payload in networks.items():
        if not isinstance(network_key, str) or not isinstance(network_payload, Mapping):
            continue
        if network_payload.get("external") is not True:
            continue
        network_name = network_payload.get("name", network_key)
        if isinstance(network_name, str) and network_name.strip():
            names.append(network_name.strip())
    return tuple(dict.fromkeys(names))


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
