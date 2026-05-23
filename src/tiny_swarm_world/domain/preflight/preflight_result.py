from __future__ import annotations

from dataclasses import dataclass

from tiny_swarm_world.domain.preflight.preflight_check import PreflightCheck


@dataclass(frozen=True)
class PreflightResult:
    checks: tuple[PreflightCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[PreflightCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "PASSED" if self.passed else "FAILED",
            "checks": [check.to_dict() for check in self.checks],
        }
