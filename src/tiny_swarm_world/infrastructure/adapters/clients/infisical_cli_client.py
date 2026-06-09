from __future__ import annotations

import shutil
import subprocess

from tiny_swarm_world.application.ports.clients.port_infisical_cli import (
    InfisicalCliResult,
    PortInfisicalCli,
)


class InfisicalCliClient(PortInfisicalCli):
    def is_available(self) -> bool:
        return shutil.which("infisical") is not None

    def run_bootstrap(self, args: tuple[str, ...]) -> InfisicalCliResult:
        result = subprocess.run(
            args,
            capture_output=True,
            check=False,
            text=True,
            timeout=300,
        )
        return InfisicalCliResult(
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
