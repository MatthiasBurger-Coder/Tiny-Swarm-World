import subprocess

from tiny_swarm_world.application.ports.clients.port_container_runtime import PortContainerRuntime
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class DockerCliRuntime(PortContainerRuntime):
    def __init__(self):
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
        self.logger.info(f"Running docker command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if check and result.returncode != 0:
            raise RuntimeError(
                f"Docker command failed with exit code {result.returncode}: {' '.join(command)}\n{result.stderr}"
            )
        return result
