from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path

from tiny_swarm_world.application.ports.host import PortHostEnvironmentDetector
from tiny_swarm_world.domain.preflight.host_environment import (
    HostEnvironmentReport,
    HostEnvironmentSignals,
    classify_host_environment,
)
from tiny_swarm_world.infrastructure.adapters.host.linux_host_signal_reader import (
    LinuxHostSignalReader,
)
from tiny_swarm_world.infrastructure.adapters.host.wsl_host_signal_reader import (
    WslHostSignalReader,
)


class HostEnvironmentDetector(PortHostEnvironmentDetector):
    """Compose focused signal readers and delegate the decision to the domain."""

    def __init__(
        self,
        *,
        os_root: Path = Path("/"),
        environment: Mapping[str, str] | None = None,
        platform_system: Callable[[], str] | None = None,
        linux_signal_reader: LinuxHostSignalReader | None = None,
        wsl_signal_reader: WslHostSignalReader | None = None,
    ) -> None:
        selected_environment = os.environ if environment is None else environment
        self.linux_signal_reader = linux_signal_reader or LinuxHostSignalReader(
            os_root=os_root,
            environment=selected_environment,
            platform_system=platform_system,
        )
        self.wsl_signal_reader = wsl_signal_reader or WslHostSignalReader(
            os_root=os_root,
            environment=selected_environment,
        )

    def detect(self) -> HostEnvironmentReport:
        linux = self.linux_signal_reader.read()
        wsl = self.wsl_signal_reader.read()
        return classify_host_environment(
            HostEnvironmentSignals(
                platform_family=linux.platform_family,
                distribution=linux.distribution,
                kernel_release=linux.kernel_release,
                proc_version=linux.proc_version,
                wsl_distribution=wsl.distribution,
                windows_interop_available=wsl.windows_interop_available,
                sandbox_signal=linux.sandbox_signal,
            )
        )
