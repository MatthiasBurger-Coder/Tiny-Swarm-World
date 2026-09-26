"""Pure local configuration boundary shared by installation and composition.

The caller owns private staging and lifecycle execution. This adapter never
runs commands or resolves credentials against a running vault.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import math
import re
from urllib.parse import urlparse
from pathlib import Path
from types import MappingProxyType

from tiny_swarm_world.domain.configuration import ConfigurationContract, default_configuration_contract
from tiny_swarm_world.domain.configuration.configuration_contract import validate_traefik_htpasswd
from tiny_swarm_world.domain.configuration.secret_manifest import SecretManifestEntry
from tiny_swarm_world.domain.deployment import ServiceStackProfile, service_stack_contracts_for_profile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight.secret_storage import assess_secret_storage
from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    DockerAptMirrorConfiguration, DockerRegistryMirrorConfiguration,
)
from tiny_swarm_world.infrastructure.adapters.configuration.configuration_sources import (
    EnvironmentConfigurationSource, ShellEnvFileConfigurationSource,
)
from tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector import ProjectFilesystemInspector
from tiny_swarm_world.infrastructure.adapters.preflight.secret_storage_probe import SecretStorageProbe
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import NodeProviderConfigYamlRepository
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import PortRegistryYamlRepository
from tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository import SecretManifestYamlRepository
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


@dataclass(frozen=True)
class InstallerConfigurationSnapshot:
    environment: Mapping[str, str] = field(repr=False)
    manifest_entries: tuple[SecretManifestEntry, ...] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "environment", MappingProxyType(dict(self.environment)))


class InstallerConfigurationRepository:
    def __init__(
        self, *, repository_root: Path, infra_root: Path,
        operator_env_file: Path | None, environment: Mapping[str, str],
        service_profile: ServiceStackProfile | str,
    ) -> None:
        self.paths = ProjectPaths.from_roots(repository_root, infra_root)
        self.operator_env_file = operator_env_file
        self.environment = dict(environment)
        self.service_profile = ServiceStackProfile(service_profile)

    def load(self) -> InstallerConfigurationSnapshot:
        """Validate copied static files; bootstrap values are checked after resolution."""
        values = (dict(ShellEnvFileConfigurationSource(self.operator_env_file).load())
                  if self.operator_env_file is not None else {})
        values.update(EnvironmentConfigurationSource(self.environment).load())
        environment = {**self.environment, **values}
        NodeProviderConfigYamlRepository(project_paths=self.paths, freeze_on_load=True).load()
        ports = PortRegistryYamlRepository(project_paths=self.paths).load()
        manifest = SecretManifestYamlRepository(
            self.paths.config_root / "secrets" / "infisical-secrets.yaml"
        ).load()
        repository = ComposeFileRepositoryYaml(
            project_paths=self.paths, port_registry=ports,
            service_profile=self.service_profile, environment=environment,
        )
        repository.validate_and_snapshot(tuple(
            item.stack_name for item in service_stack_contracts_for_profile(self.service_profile)
        ))
        return InstallerConfigurationSnapshot(environment, manifest)

    @staticmethod
    def validate_operator_source(path: Path, host_environment: HostEnvironmentKind) -> None:
        """Apply the existing secret-storage policy to the original input location."""
        if any(item.is_symlink() for item in (path, *path.parents)):
            raise ValueError("Operator configuration must not use symbolic links.")
        probe = SecretStorageProbe(ProjectFilesystemInspector())
        inspection = probe.inspect(str(path), host_environment)
        uid, gid = probe.effective_identity()
        assessment = assess_secret_storage(
            host_environment, inspection, expected_uid=uid, expected_gid=gid,
            require_existing_file=False,
        )
        if not assessment.allowed:
            raise ValueError("Operator configuration storage is unsafe.")

    @staticmethod
    def validate_environment(
        environment: Mapping[str, str], *, stack_names: tuple[str, ...],
        include_setup: bool = False, deferred_keys: tuple[str, ...] = (),
    ) -> None:
        """Validate effective inputs; deferral is explicit and consumer-specific."""
        scopes = {*stack_names, "deployment"}
        for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS):
            if contract.stack_name in stack_names:
                scopes.update(contract.required_services)
        if include_setup:
            scopes.add("platform")
        requirements = tuple(
            replace(item, required=False) if item.key in deferred_keys else item
            for item in default_configuration_contract().requirements
            if item.scope in scopes
        )
        values = {
            key: ("" if value.startswith("<operator-supplied:") else value)
            for key, value in environment.items()
        }
        result = ConfigurationContract("1", requirements).validate(values)
        if not result.passed:
            raise ValueError("Selected operator configuration is invalid: " + ", ".join(
                finding.key for finding in result.failed_findings
            ))
        if "traefik" in stack_names and environment.get("TSW_TRAEFIK_GUI_USERS_HTPASSWD"):
            validate_traefik_htpasswd(environment["TSW_TRAEFIK_GUI_USERS_HTPASSWD"])
        if include_setup:
            _number(environment, "TSW_SETUP_WORKFLOW_TIMEOUT_SECONDS", 1)
            _number(environment, "TSW_SETUP_HEARTBEAT_INTERVAL_SECONDS", 1)
            _number(environment, "TSW_SETUP_MAX_CONCURRENCY", 1, integer=True)
            _number(environment, "TSW_WINDOWS_BRIDGE_TIMEOUT_SECONDS", 1)
            if (environment.get("TSW_LXC_PROXY_LISTEN_ADDRESS") or "0.0.0.0").strip() not in {"127.0.0.1", "0.0.0.0"}:
                raise ValueError("LXC proxy listen address must be 127.0.0.1 or 0.0.0.0.")
            mirror = environment.get("TSW_LXC_DOCKER_REGISTRY_MIRROR", "").strip()
            if mirror:
                configuration = DockerRegistryMirrorConfiguration(mirror)
                _ = configuration.registry_authority
            DockerAptMirrorConfiguration(*(
                environment.get(name, "").strip() or None for name in (
                    "TSW_LXC_UBUNTU_APT_MIRROR", "TSW_LXC_UBUNTU_SECURITY_APT_MIRROR",
                    "TSW_LXC_DOCKER_APT_MIRROR", "TSW_LXC_DOCKER_APT_GPG_URL",
                )
            ))
        if "infisical" in stack_names:
            mode = (environment.get("TSW_INFISICAL_PROVIDER_MODE") or "self_hosted").strip().lower()
            if mode != "self_hosted":
                raise ValueError("Selected Infisical provider mode is unsupported.")
            parsed = urlparse((environment.get("TSW_INFISICAL_URL") or "http://localhost:17080").strip())
            if (parsed.scheme not in {"http", "https"}
                    or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                    or parsed.username is not None or parsed.password is not None):
                raise ValueError("Selected Infisical bootstrap URL is invalid.")
            _ = parsed.port
            _number(environment, "TSW_INFISICAL_READINESS_ATTEMPTS", 1, integer=True)
            _number(environment, "TSW_INFISICAL_READINESS_INTERVAL_SECONDS", 0)
        if include_setup or any(name in stack_names for name in ("jenkins", "service-access", "nexus")):
            endpoint = (environment.get("TSW_SWARM_REGISTRY_ENDPOINT") or "127.0.0.1:13500").strip()
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*(?::\d{1,5})?", endpoint):
                raise ValueError("Swarm registry endpoint must be host[:port] without scheme or credentials.")
        if "nexus" in stack_names:
            if not (environment.get("TSW_NEXUS_DOCKER_HUB_PROXY_REPOSITORY") or "docker-hub-proxy").strip():
                raise ValueError("Nexus Docker proxy repository name must not be empty.")
            raw_port = (environment.get("TSW_NEXUS_DOCKER_HUB_PROXY_PORT") or "5001").strip()
            try:
                port = int(raw_port, 10)
            except ValueError:
                raise ValueError("TSW_NEXUS_DOCKER_HUB_PROXY_PORT must be a valid TCP port.") from None
            if port <= 0 or port > 65535:
                raise ValueError("TSW_NEXUS_DOCKER_HUB_PROXY_PORT must be a valid TCP port.")


def _number(
    environment: Mapping[str, str], key: str, minimum: int, *, integer: bool = False,
) -> float | None:
    value = environment.get(key, "").strip()
    if not value:
        return None
    try:
        parsed = int(value, 10) if integer else float(value)
    except ValueError:
        raise ValueError(f"{key} has an invalid numeric value.") from None
    if (isinstance(parsed, float) and not math.isfinite(parsed)) or parsed < minimum:
        raise ValueError(f"{key} has an invalid numeric value.")
    return parsed
