from __future__ import annotations

import re
import shlex
import subprocess
from collections.abc import Mapping

from tiny_swarm_world.application.ports.clients.port_swarm_stack_runtime import (
    PortSwarmStackRuntime,
    SwarmServiceStatus,
)
from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import infra_root


REPLICA_PATTERN = re.compile(r"^(?P<current>\d+)/(?:\s*)?(?P<desired>\d+)$")
STACK_ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


class MultipassSwarmRuntime(PortSwarmStackRuntime):
    def __init__(
        self,
        manager_vm: str = "swarm-manager",
        remote_stack_root: str = "/tmp/tiny-swarm-world/stacks",
        timeout_seconds: int = 900,
    ):
        if timeout_seconds <= 0:
            raise ValueError("Swarm runtime timeout must be positive.")
        self.manager_vm = manager_vm
        self.remote_stack_root = remote_stack_root.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def deploy_stack(
        self,
        stack_definition: StackDefinition,
        stack_environment: Mapping[str, str] | None = None,
    ) -> None:
        self._ensure_stack_prerequisites(stack_definition.name)
        remote_dir = f"{self.remote_stack_root}/{stack_definition.name}"
        compose_path = f"{remote_dir}/docker-compose.yml"
        script = (
            f"set -e; mkdir -p {shlex.quote(remote_dir)}; "
            f"cat > {shlex.quote(compose_path)}"
        )
        self._run_manager_shell(script, input_text=stack_definition.compose_content)
        self._transfer_stack_assets(stack_definition.name, remote_dir)
        environment = {
            "TSW_REMOTE_STACK_ROOT": self.remote_stack_root,
            **dict(stack_environment or {}),
        }
        self._run_manager_shell(
            f"{_stack_environment_prefix(environment)} "
            f"docker stack deploy --detach=true -c {shlex.quote(compose_path)} "
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
            f"docker secret inspect {shlex.quote(name)} >/dev/null 2>&1",
            check=False,
        )
        return result.returncode == 0

    def _ensure_stack_prerequisites(self, stack_name: str) -> None:
        if stack_name != "sonarqube":
            return
        self._run_manager_shell(
            "sudo sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null",
        )

    def _transfer_stack_assets(self, stack_name: str, remote_dir: str) -> None:
        if stack_name != "swagger":
            return
        openapi_file = infra_root() / "compose" / "swagger" / "swagger" / "openapi.json"
        nginx_config = infra_root() / "compose" / "swagger" / "nginx" / "default.conf"
        script = (
            f"set -e; mkdir -p {shlex.quote(remote_dir + '/swagger')}; "
            f"cat > {shlex.quote(remote_dir + '/swagger/openapi.json')}"
        )
        self._run_manager_shell(script, input_text=openapi_file.read_text(encoding="utf-8"))
        script = (
            f"set -e; mkdir -p {shlex.quote(remote_dir + '/nginx')}; "
            f"cat > {shlex.quote(remote_dir + '/nginx/default.conf')}"
        )
        self._run_manager_shell(script, input_text=nginx_config.read_text(encoding="utf-8"))

    def _run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.logger.info("Running manager shell operation.")
        try:
            result = subprocess.run(
                ["multipass", "exec", self.manager_vm, "--", "sh", "-lc", script],
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Manager Swarm operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(f"Manager Swarm operation failed with exit code {result.returncode}.")
        return result


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


def _stack_environment_prefix(environment: Mapping[str, str]) -> str:
    assignments: list[str] = []
    for name, value in sorted(environment.items()):
        if not STACK_ENVIRONMENT_NAME_PATTERN.fullmatch(name):
            raise ValueError("Stack environment name contains invalid characters.")
        assignments.append(f"{name}={shlex.quote(str(value))}")
    return " ".join(assignments)
