"""Gateway for executing bounded shell operations in managed LXC nodes."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from logging import Logger

from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.diagnostics import (
    is_transient_manager_shell_failure,
    safe_log_text,
)
from tiny_swarm_world.infrastructure.process import (
    ProcessRunner,
    SubprocessProcessRunner,
)


_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_MAX_ATTEMPTS = 3
_RETRY_DELAYS_SECONDS = (0.5, 1.0)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
Sleeper = Callable[[float], None]


class LxcManagerShellGateway:
    """Execute manager and node shell commands through Incus or LXD."""

    def __init__(
        self,
        *,
        backend: ManagedLxcBackend,
        manager_node: str,
        timeout_seconds: int,
        logger: Logger,
        process_runner: ProcessRunner | None = None,
    ) -> None:
        self.backend = backend
        self.manager_node = manager_node
        self.timeout_seconds = timeout_seconds
        self.logger = logger
        self.process_runner = process_runner or SubprocessProcessRunner()

    def run_manager_shell(
        self,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        timeout_seconds: int | None = None,
        run: CommandRunner | None = None,
        sleep: Sleeper | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command on the configured manager node."""

        return self.run_node_shell(
            self.manager_node,
            script,
            check=check,
            input_text=input_text,
            timeout_seconds=timeout_seconds,
            run=run,
            sleep=sleep,
        )

    def run_node_shell(
        self,
        node_name: str,
        script: str,
        *,
        check: bool = True,
        input_text: str | None = None,
        timeout_seconds: int | None = None,
        run: CommandRunner | None = None,
        sleep: Sleeper | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command on an LXC node with bounded retry behavior."""

        sleeper = sleep or time.sleep
        shell_target = "manager" if node_name == self.manager_node else "node"
        self.logger.info(
            "Running LXC %s shell operation node=%s script=%s",
            shell_target,
            node_name,
            safe_log_text(script),
        )
        timeout = timeout_seconds or self.timeout_seconds
        shell_scope = "manager_shell" if node_name == self.manager_node else "node_shell"
        result: subprocess.CompletedProcess[str] | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            result = self._run_once(
                run,
                node_name,
                script,
                input_text=input_text,
                timeout=timeout,
            )
            self._log_result(shell_scope, node_name, result)
            if not self._retry_if_needed(result, attempt, node_name, sleeper):
                break
        if result is None:
            raise RuntimeError("LXC node Swarm operation did not execute.")
        if check and result.returncode != 0:
            raise RuntimeError(f"LXC node Swarm operation failed with exit code {result.returncode}.")
        return result

    def _run_once(
        self,
        runner: CommandRunner | None,
        node_name: str,
        script: str,
        *,
        input_text: str | None,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        try:
            command = [_BACKEND_CLI[self.backend], "exec", node_name, "--", "sh", "-lc", script]
            if runner is None:
                return subprocess.run(
                    command,
                    input=input_text,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=False,
                    timeout=timeout,
                )
            return runner(
                command,
                input=input_text,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"LXC Swarm operation timed out on node '{node_name}'."
            ) from exc

    def _log_result(
        self,
        shell_scope: str,
        node_name: str,
        result: subprocess.CompletedProcess[str],
    ) -> None:
        log = self.logger.warning if result.returncode != 0 else self.logger.info
        log(
            "lxc_swarm_runtime %s_result returncode=%s node=%s stdout=%s stderr=%s",
            shell_scope,
            result.returncode,
            node_name,
            safe_log_text(result.stdout),
            safe_log_text(result.stderr),
        )

    def _retry_if_needed(
        self,
        result: subprocess.CompletedProcess[str],
        attempt: int,
        node_name: str,
        sleeper: Sleeper,
    ) -> bool:
        if not is_transient_manager_shell_failure(result) or attempt >= _MAX_ATTEMPTS:
            return False
        delay_seconds = _RETRY_DELAYS_SECONDS[
            min(attempt - 1, len(_RETRY_DELAYS_SECONDS) - 1)
        ]
        self.logger.warning(
            "Retrying transient LXC node shell operation after Incus child PID failure "
            "node=%s attempt=%s next_attempt=%s delay_seconds=%s",
            node_name,
            attempt,
            attempt + 1,
            delay_seconds,
        )
        sleeper(delay_seconds)
        return True
