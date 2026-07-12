from __future__ import annotations

from tiny_swarm_world.application.ports.host import PortHostEnvironmentDetector
from tiny_swarm_world.domain.preflight.host_environment import HostEnvironmentReport


class DetectHostEnvironment:
    def __init__(self, detector: PortHostEnvironmentDetector) -> None:
        self.detector = detector

    def run(self) -> HostEnvironmentReport:
        return self.detector.detect()
