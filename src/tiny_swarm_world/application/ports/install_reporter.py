from __future__ import annotations

from typing import Protocol

from tiny_swarm_world.domain.install import InstallEvent


class InstallReporter(Protocol):
    def report(self, event: InstallEvent) -> None:
        ...
