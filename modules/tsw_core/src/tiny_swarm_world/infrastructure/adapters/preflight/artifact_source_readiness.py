from __future__ import annotations

import os
import hashlib
import json
import socket
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from tiny_swarm_world.application.ports.preflight import PortArtifactSourceReadiness
from tiny_swarm_world.domain.preflight.artifact_sources import (
    ArtifactSourceAttempt,
    ArtifactSourceReadiness,
    ArtifactSourceStatus,
)


DEFAULT_SOURCE_MODE = "direct-internet"
DEFAULT_TIMEOUT_SECONDS = 10.0
SOURCE_MODE_ENVIRONMENT = "TSW_ARTIFACT_SOURCE_MODE"
SOURCE_TIMEOUT_ENVIRONMENT = "TSW_ARTIFACT_SOURCE_TIMEOUT_SECONDS"
REGISTRY_MIRROR_ENVIRONMENT = "TSW_LXC_DOCKER_REGISTRY_MIRROR"
UBUNTU_ARCHIVE_ENVIRONMENT = "TSW_LXC_UBUNTU_APT_MIRROR"
UBUNTU_SECURITY_ENVIRONMENT = "TSW_LXC_UBUNTU_SECURITY_APT_MIRROR"
DOCKER_APT_ENVIRONMENT = "TSW_LXC_DOCKER_APT_MIRROR"
DOCKER_GPG_ENVIRONMENT = "TSW_LXC_DOCKER_APT_GPG_URL"
OFFLINE_MANIFEST_ENVIRONMENT = "TSW_OFFLINE_ARTIFACT_MANIFEST"


@dataclass(frozen=True)
class _SourceTarget:
    source: str
    kind: str
    probe_url: str


class HttpArtifactSourceReadiness(PortArtifactSourceReadiness):
    """Bounded, read-only checks for the package and image source families."""

    def __init__(
        self,
        *,
        environment: dict[str, str] | None = None,
        opener: Callable[..., object] | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        values = environment or dict(os.environ)
        self._environment = values
        self.mode = values.get(SOURCE_MODE_ENVIRONMENT, DEFAULT_SOURCE_MODE).strip().lower()
        if self.mode not in {"direct-internet", "nexus", "fallback", "offline"}:
            raise ValueError(
                f"{SOURCE_MODE_ENVIRONMENT} must be direct-internet, nexus, fallback, or offline."
            )
        raw_timeout = timeout_seconds
        if raw_timeout is None:
            raw_timeout = float(values.get(SOURCE_TIMEOUT_ENVIRONMENT, str(DEFAULT_TIMEOUT_SECONDS)))
        if raw_timeout <= 0:
            raise ValueError("Artifact source readiness timeout must be positive.")
        self.timeout_seconds = raw_timeout
        self._opener = opener or urllib.request.urlopen
        self._groups = _target_groups(values, self.mode)

    def check(self) -> ArtifactSourceReadiness:
        if self.mode == "offline":
            return self._check_offline_manifest()

        attempts: list[ArtifactSourceAttempt] = []
        for group_name, targets in self._groups:
            group_attempts = [self._probe(target) for target in targets]
            attempts.extend(group_attempts)
            if group_attempts and all(
                attempt.status is ArtifactSourceStatus.READY
                for attempt in group_attempts
            ):
                return ArtifactSourceReadiness(self.mode, group_name, tuple(group_attempts))
        return ArtifactSourceReadiness(self.mode, None, tuple(attempts))

    def _check_offline_manifest(self) -> ArtifactSourceReadiness:
        manifest_value = self._environment.get(OFFLINE_MANIFEST_ENVIRONMENT, "").strip()
        if not manifest_value:
            return _failed_offline_readiness("offline manifest is not configured")
        manifest_path = Path(manifest_value).expanduser()
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return _failed_offline_readiness("offline manifest is missing")
        except (OSError, UnicodeError, json.JSONDecodeError):
            return _failed_offline_readiness("offline manifest is unreadable")
        if not isinstance(payload, dict) or payload.get("contract_version") != 1:
            return _failed_offline_readiness("offline manifest contract is invalid")
        raw_artifacts = payload.get("artifacts")
        if not isinstance(raw_artifacts, list) or not raw_artifacts:
            return _failed_offline_readiness("offline manifest has no artifacts")

        attempts: list[ArtifactSourceAttempt] = []
        for raw_artifact in raw_artifacts:
            attempt = _verify_offline_artifact(manifest_path, raw_artifact)
            attempts.append(attempt)
        if all(attempt.status is ArtifactSourceStatus.READY for attempt in attempts):
            return ArtifactSourceReadiness(self.mode, "offline", tuple(attempts))
        return ArtifactSourceReadiness(self.mode, None, tuple(attempts))

    def _probe(self, target: _SourceTarget) -> ArtifactSourceAttempt:
        try:
            response = self._opener(target.probe_url, timeout=self.timeout_seconds)
            status_value = getattr(response, "status", None)
            if status_value is None:
                get_code = getattr(response, "getcode", None)
                if not callable(get_code):
                    raise OSError("source response has no status")
                status_value = get_code()
            status = int(status_value)
            close = getattr(response, "close", None)
            if callable(close):
                close()
            if 200 <= status < 500:
                return ArtifactSourceAttempt(
                    target.source,
                    target.kind,
                    ArtifactSourceStatus.READY,
                    f"HTTP {status}",
                )
            return ArtifactSourceAttempt(
                target.source,
                target.kind,
                ArtifactSourceStatus.FAILED,
                f"HTTP {status}",
            )
        except (TimeoutError, socket.timeout):
            return ArtifactSourceAttempt(
                target.source,
                target.kind,
                ArtifactSourceStatus.TIMED_OUT,
                "connect or response timeout",
            )
        except urllib.error.HTTPError as exc:
            if target.kind in {"docker-registry", "docker-registry-mirror"} and 400 <= exc.code < 500:
                return ArtifactSourceAttempt(
                    target.source,
                    target.kind,
                    ArtifactSourceStatus.READY,
                    f"HTTP {exc.code} (registry authentication challenge)",
                )
            return ArtifactSourceAttempt(
                target.source,
                target.kind,
                ArtifactSourceStatus.FAILED,
                f"HTTP {exc.code}",
            )
        except (OSError, urllib.error.URLError) as exc:
            return ArtifactSourceAttempt(
                target.source,
                target.kind,
                ArtifactSourceStatus.FAILED,
                _safe_error(exc),
            )


def _failed_offline_readiness(detail: str) -> ArtifactSourceReadiness:
    return ArtifactSourceReadiness(
        "offline",
        None,
        (
            ArtifactSourceAttempt(
                "offline",
                "offline-manifest",
                ArtifactSourceStatus.FAILED,
                detail,
            ),
        ),
    )


def _verify_offline_artifact(
    manifest_path: Path,
    raw_artifact: object,
) -> ArtifactSourceAttempt:
    if not isinstance(raw_artifact, dict):
        return ArtifactSourceAttempt(
            "offline",
            "offline-artifact",
            ArtifactSourceStatus.FAILED,
            "offline artifact entry is invalid",
        )
    artifact_id = str(raw_artifact.get("id", "")).strip()
    relative_path = str(raw_artifact.get("path", "")).strip()
    expected_hash = str(raw_artifact.get("sha256", "")).strip().lower()
    if not artifact_id or not relative_path or not re_full_sha256(expected_hash):
        return ArtifactSourceAttempt(
            artifact_id or "offline",
            "offline-artifact",
            ArtifactSourceStatus.FAILED,
            "offline artifact requires id, path and sha256",
        )
    artifact_path = Path(relative_path).expanduser()
    if not artifact_path.is_absolute():
        artifact_path = manifest_path.parent / artifact_path
    try:
        actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return ArtifactSourceAttempt(
            artifact_id,
            "offline-artifact",
            ArtifactSourceStatus.FAILED,
            "offline artifact file is missing or unreadable",
        )
    if actual_hash != expected_hash:
        return ArtifactSourceAttempt(
            artifact_id,
            "offline-artifact",
            ArtifactSourceStatus.FAILED,
            "offline artifact checksum mismatch",
        )
    return ArtifactSourceAttempt(
        artifact_id,
        "offline-artifact",
        ArtifactSourceStatus.READY,
        "offline artifact checksum verified",
    )


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _target_groups(
    values: dict[str, str],
    mode: str,
) -> tuple[tuple[str, tuple[_SourceTarget, ...]], ...]:
    direct = _direct_targets(values)
    mirror = values.get(REGISTRY_MIRROR_ENVIRONMENT, "").strip()
    nexus = _nexus_targets(values, mirror) if mirror else ()
    if mode == "direct-internet":
        return (("direct-internet", direct),)
    if mode == "nexus":
        return (("nexus", nexus),)
    if mode == "fallback":
        groups: list[tuple[str, tuple[_SourceTarget, ...]]] = []
        if nexus:
            groups.append(("nexus", nexus))
        groups.append(("direct-internet", direct))
        return tuple(groups)
    return ()


def _direct_targets(values: dict[str, str]) -> tuple[_SourceTarget, ...]:
    return (
        _target("https://registry-1.docker.io", "docker-registry", "/v2/"),
        _target(
            values.get(UBUNTU_ARCHIVE_ENVIRONMENT, "https://archive.ubuntu.com/ubuntu"),
            "ubuntu-apt",
            "/dists/noble/InRelease",
        ),
        _target(
            values.get(DOCKER_APT_ENVIRONMENT, "https://download.docker.com/linux/ubuntu"),
            "docker-apt",
            "/dists/noble/stable/binary-amd64/Packages.gz",
        ),
        _target(
            values.get(DOCKER_GPG_ENVIRONMENT, "https://download.docker.com/linux/ubuntu/gpg"),
            "docker-apt-gpg",
            "",
        ),
    )


def _nexus_targets(values: dict[str, str], mirror: str) -> tuple[_SourceTarget, ...]:
    return (
        _target(mirror, "docker-registry-mirror", "/v2/"),
        _target(
            values.get(UBUNTU_ARCHIVE_ENVIRONMENT, "https://archive.ubuntu.com/ubuntu"),
            "ubuntu-apt",
            "/dists/noble/InRelease",
        ),
        _target(
            values.get(DOCKER_APT_ENVIRONMENT, "https://download.docker.com/linux/ubuntu"),
            "docker-apt",
            "/dists/noble/stable/binary-amd64/Packages.gz",
        ),
        _target(
            values.get(DOCKER_GPG_ENVIRONMENT, "https://download.docker.com/linux/ubuntu/gpg"),
            "docker-apt-gpg",
            "",
        ),
    )


def _target(source: str, kind: str, suffix: str) -> _SourceTarget:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"Configured {kind} source must be an absolute HTTP(S) URL.")
    probe_url = source if not suffix else urljoin(source.rstrip("/") + "/", suffix.lstrip("/"))
    return _SourceTarget(source, kind, probe_url)


def _safe_error(error: BaseException) -> str:
    return type(error).__name__
