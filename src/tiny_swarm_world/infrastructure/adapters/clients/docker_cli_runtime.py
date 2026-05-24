import subprocess

from tiny_swarm_world.application.ports.clients.port_container_runtime import PortContainerRuntime
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class DockerCliRuntime(PortContainerRuntime):
    def __init__(self, timeout_seconds: int = 30):
        if timeout_seconds <= 0:
            raise ValueError("Docker runtime timeout must be positive.")
        self.timeout_seconds = timeout_seconds
        self.logger = LoggerFactory.get_logger(self.__class__)

    def find_container_names(self, name_filter: str) -> list[str]:
        result = self._run_command(
            ["docker", "ps", "--filter", f"name={name_filter}", "--format", "{{.Names}}"],
            check=False,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def file_exists(self, container_name: str, file_path: str) -> bool:
        result = self._run_command(["docker", "exec", container_name, "test", "-f", file_path], check=False)
        return result.returncode == 0

    def read_file(self, container_name: str, file_path: str) -> str:
        result = self._run_command(["docker", "exec", container_name, "cat", file_path], check=True)
        return result.stdout

    def _run_command(self, command: list[str], check: bool) -> subprocess.CompletedProcess[str]:
        operation = command[1] if len(command) > 1 else "operation"
        self.logger.info("Running Docker runtime operation '%s'.", operation)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Docker runtime operation timed out.") from exc
        if check and result.returncode != 0:
            raise RuntimeError(f"Docker runtime operation failed with exit code {result.returncode}.")
        return result
