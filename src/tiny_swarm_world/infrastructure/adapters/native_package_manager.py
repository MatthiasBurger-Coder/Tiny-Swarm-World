"""Bounded APT operations for qualified Ubuntu hosts only."""

from __future__ import annotations

import os

from tiny_swarm_world.infrastructure.process import (
    ProcessLaunchError,
    ProcessRunner,
    ProcessTimeoutError,
    SubprocessProcessRunner,
)


class AptHostPackageManager:
    def __init__(self, runner: ProcessRunner | None = None) -> None:
        self._runner = runner or SubprocessProcessRunner()

    def missing(self, packages: tuple[str, ...]) -> tuple[str, ...]:
        missing: list[str] = []
        for package in packages:
            try:
                result = self._runner.run_text(
                    ("dpkg-query", "--show", "--showformat=${Status}", "--", package),
                    timeout=10.0,
                )
            except (ProcessLaunchError, ProcessTimeoutError) as error:
                raise RuntimeError("Host package inventory could not be read.") from error
            if result.returncode != 0 or result.stdout.strip() != "install ok installed":
                missing.append(package)
        return tuple(missing)

    def install(self, packages: tuple[str, ...]) -> None:
        if not packages:
            return
        prefix = () if os.geteuid() == 0 else ("sudo",)
        try:
            update = self._runner.run_text(
                (*prefix, "apt-get", "update"),
                timeout=900.0,
                capture_output=True,
            )
            if update.returncode != 0:
                raise RuntimeError("APT index update failed; inspect package sources and retry.")
            install = self._runner.run_text(
                (
                    *prefix,
                    "apt-get",
                    "install",
                    "--yes",
                    "--no-install-recommends",
                    "--no-upgrade",
                    "--",
                    *packages,
                ),
                timeout=1800.0,
                capture_output=True,
            )
            if install.returncode != 0:
                raise RuntimeError("APT package installation failed; inspect APT and retry preparation.")
        except (ProcessLaunchError, ProcessTimeoutError) as error:
            raise RuntimeError("APT command could not finish; inspect package state before retry.") from error
