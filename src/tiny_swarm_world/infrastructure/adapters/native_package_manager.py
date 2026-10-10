"""Bounded APT operations for qualified Ubuntu hosts only."""

from __future__ import annotations

import os
import re

from tiny_swarm_world.application.ports.native_preparation import (
    HostPackagePreparationFailure, PackageCandidateConsent, PreparationTargetSnapshot,
)

from tiny_swarm_world.infrastructure.process import (
    ProcessLaunchError,
    ProcessRunner,
    ProcessTimeoutError,
    SubprocessProcessRunner,
)


class AptHostPackageManager:
    def __init__(
        self, runner: ProcessRunner | None = None, *,
        candidate_consent: PackageCandidateConsent | None = None,
        target_snapshot: PreparationTargetSnapshot | None = None,
    ) -> None:
        self._runner = runner or SubprocessProcessRunner()
        self._candidate_consent = candidate_consent
        self._target_snapshot = target_snapshot

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
        snapshot = self._target_snapshot() if self._target_snapshot else None
        prefix = () if os.geteuid() == 0 else ("sudo", "-n")
        stage = "apt_index_refresh"
        try:
            update = self._runner.run_text(
                (*prefix, "apt-get", "update",
                 "-o", "DPkg::Lock::Timeout=30",
                 "-o", "Acquire::Retries=0",
                 "-o", "Acquire::http::Timeout=30",
                 "-o", "Acquire::https::Timeout=30",
                 "-o", "APT::Update::Error-Mode=any"),
                timeout=900.0,
                capture_output=True,
            )
            if update.returncode != 0:
                raise HostPackagePreparationFailure(stage, update.returncode, "APT index update failed; inspect connectivity/package locks, then rerun ./prepare_linux.sh --dry-run.")
            if self._candidate_consent is not None:
                stage = "apt_candidates"
                try:
                    packages = self._approved_candidates(packages, snapshot)
                except RuntimeError:
                    raise HostPackagePreparationFailure(stage, 4, "Package consent or candidate verification failed after index refresh.") from None
            stage = "apt_install"
            install = self._runner.run_text(
                (
                    *prefix,
                    "apt-get",
                    "install",
                    "-o", "DPkg::Lock::Timeout=30",
                    "-o", "Acquire::Retries=0",
                    "-o", "Acquire::http::Timeout=30",
                    "-o", "Acquire::https::Timeout=30",
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
                raise HostPackagePreparationFailure(stage, install.returncode, "APT package installation failed; inspect APT locks/connectivity, then rerun ./prepare_linux.sh --dry-run.")
        except (ProcessLaunchError, ProcessTimeoutError) as error:
            raise HostPackagePreparationFailure(stage, 124 if isinstance(error, ProcessTimeoutError) else 1,
                                                "APT command could not finish; inspect package state before retry.") from None


    def _candidates(self, packages: tuple[str, ...]) -> tuple[str, ...]:
        candidates: list[str] = []
        for package in packages:
            result = self._runner.run_text(("apt-cache", "policy", "--", package), timeout=10.0)
            versions = [line.strip().partition(":")[2].strip()
                        for line in result.stdout.splitlines() if line.strip().startswith("Candidate:")]
            if result.returncode or len(versions) != 1 or not re.fullmatch(r"[A-Za-z0-9.+:~_-]+", versions[0]):
                raise RuntimeError("Package candidate unavailable after index refresh; retry ./prepare_linux.sh --dry-run.")
            candidates.append(f"{package}={versions[0]}")
        return tuple(candidates)

    def _approved_candidates(self, packages: tuple[str, ...], snapshot: object) -> tuple[str, ...]:
        candidates = self._candidates(packages)
        assert self._candidate_consent is not None
        if not self._candidate_consent(candidates):
            raise RuntimeError("Package consent declined after APT index refresh; no packages installed.")
        if self._target_snapshot and self._target_snapshot() != snapshot:
            raise RuntimeError("Host target changed after consent; review ./prepare_linux.sh --dry-run.")
        if self.missing(packages) != packages or self._candidates(packages) != candidates:
            raise RuntimeError("Package plan or candidates changed after consent; review again.")
        return candidates


def confirm_apt_candidates(candidates: tuple[str, ...]) -> bool:
    print("APT index refresh completed. Ubuntu candidates: " + ", ".join(candidates))
    print("Install timeout: 1800s; package lock: 30s; download timeout: 30s; retries: 0.")
    try:
        return input("Install these exact candidates? Type 'yes': ") == "yes"
    except EOFError:
        return False
