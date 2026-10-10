"""Configuration responsibilities for the live installation boundary."""

from __future__ import annotations
from contextlib import AbstractContextManager
import os
import shutil
import subprocess
import sys
import stat
import tempfile
from contextlib import contextmanager
from collections.abc import Iterator
from collections.abc import Mapping
from pathlib import Path
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.infrastructure.adapters.host import ProjectFilesystemInspector
from tiny_swarm_world.domain.configuration.credential_resolution import (
    CredentialResolutionError,
)
from tiny_swarm_world.application.ports.installation import (
    DEFAULT_NATIVE_LINUX_VENV,
    DEFAULT_SECRET_ENV_FILE,
    HostRuntime,
    InstallerError,
    InstallerOptions,
    InstallerPaths,
    InstallerSecretEntry,
)


def _validate_native_installation_read_only(
    options: InstallerOptions,
    env: Mapping[str, str],
    cwd: Path,
    host_runtime: HostRuntime,
) -> None:
    from tiny_swarm_world.infrastructure.adapters.installation.credentials import (
        _ensure_default_config_exports,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.credentials import (
        _normalize_infisical_login_email,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.credentials import (
        _require_operator_provisioned_traefik_gui_users,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.credentials import (
        _resolve_internal_test_installer_values,
    )
    from tiny_swarm_world.infrastructure.adapters.installation.process import (
        _run_installer_subprocess,
    )
    from tiny_swarm_world.infrastructure.adapters.repositories.installer_configuration_repository import (
        InstallerConfigurationRepository,
    )
    from tiny_swarm_world.domain.deployment import service_stack_contracts_for_profile

    def absolute(value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else cwd / path

    repository = absolute(env.get("TSW_REPOSITORY_ROOT", str(cwd)))
    infra = absolute(env.get("TSW_INFRA_ROOT", str(repository / "infra")))
    operator_file = _paths_from_env(env, cwd).secret_env_file
    host_environment = (
        host_runtime.environment_report.environment
        if host_runtime.environment_report is not None
        else HostEnvironmentKind(host_runtime.name)
    )
    try:
        InstallerConfigurationRepository.validate_operator_source(
            operator_file, host_environment
        )
        snapshot = InstallerConfigurationRepository(
            repository_root=repository,
            infra_root=infra,
            operator_env_file=operator_file,
            environment=env,
            service_profile=options.service_profile,
        ).load()
        effective = dict(snapshot.environment)
        resolutions = _resolve_internal_test_installer_values(
            effective,
            tuple(
                InstallerSecretEntry(item.key, item.source, item.required, item.type)
                for item in snapshot.manifest_entries
                if item.required and item.source != "external_user_secret"
            ),
        )
        effective.update(resolutions.values)
        _normalize_infisical_login_email(effective)
        _ensure_default_config_exports(effective)
        _require_operator_provisioned_traefik_gui_users(effective, operator_file)
        InstallerConfigurationRepository.validate_environment(
            effective,
            stack_names=tuple(
                item.stack_name
                for item in service_stack_contracts_for_profile(options.service_profile)
            ),
            include_setup=True,
        )
    except (
        ValueError,
        OSError,
        UnicodeError,
        OperationError,
        CredentialResolutionError,
    ) as error:
        raise InstallerError(
            "Native configuration or credential preflight failed."
        ) from error
    try:
        result = _run_installer_subprocess(
            (
                sys.executable,
                "-m",
                "tiny_swarm_world",
                "setup",
                "run",
                "--preflight",
                "--service-profile",
                options.service_profile,
            ),
            env={**effective, "TSW_READ_ONLY_PREFLIGHT": "1"},
            check=False,
            timeout_seconds=120.0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, ValueError) as error:
        raise InstallerError("Native setup preflight could not be launched.") from error
    if result.returncode != 0:
        raise InstallerError(
            "Native setup preflight failed; run the setup preflight command for diagnostics."
        )


@contextmanager
def _configuration_snapshot(
    options: InstallerOptions,
    env: Mapping[str, str],
    cwd: Path,
    host_runtime: HostRuntime,
) -> Iterator[dict[str, str]]:
    from tiny_swarm_world.infrastructure.adapters.installation.host import (
        _windows_exposure_required,
    )
    from tiny_swarm_world.infrastructure.adapters.repositories.installer_configuration_repository import (
        InstallerConfigurationRepository,
    )

    def absolute(value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else cwd / path

    repository = absolute(env.get("TSW_REPOSITORY_ROOT", str(cwd)))
    infra = absolute(env.get("TSW_INFRA_ROOT", str(repository / "infra")))
    original_env_file = _paths_from_env(env, cwd).secret_env_file
    with tempfile.TemporaryDirectory(prefix="tsw-configuration-") as directory:
        try:
            host_environment = (
                host_runtime.environment_report.environment
                if host_runtime.environment_report is not None
                else HostEnvironmentKind(host_runtime.name)
            )
            InstallerConfigurationRepository.validate_operator_source(
                original_env_file, host_environment
            )
            snapshot_root = Path(directory)
            _validate_snapshot_storage(snapshot_root, host_environment)
            _copy_configuration_tree(infra / "config", snapshot_root / "config")
            prepared = dict(env)
            prepared["TSW_REPOSITORY_ROOT"] = str(repository)
            prepared["TSW_INFRA_ROOT"] = str(snapshot_root)
            staged_env_file = snapshot_root / "operator.env"
            if original_env_file.exists():
                _copy_configuration_file(
                    original_env_file, staged_env_file, secure=True
                )
                InstallerConfigurationRepository.validate_operator_source(
                    staged_env_file,
                    host_environment,
                )
            # Missing optional input stays absent even if the original later appears.
            prepared["TSW_INSTALL_ENV_FILE"] = str(staged_env_file)
            snapshot = InstallerConfigurationRepository(
                repository_root=repository,
                infra_root=snapshot_root,
                operator_env_file=staged_env_file,
                environment=prepared,
                service_profile=options.service_profile,
            ).load()
        except (ValueError, OSError, UnicodeError):
            raise InstallerError(
                "Installation configuration could not be safely prepared."
            ) from None
        prepared = dict(snapshot.environment)
        bridge_registry = prepared.get("TSW_WINDOWS_BRIDGE_PORT_REGISTRY_PATH", "")
        if (
            host_runtime.name == "wsl2"
            and _windows_exposure_required(prepared)
            and bridge_registry
        ):
            try:
                from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
                    PortRegistryYamlRepository,
                )

                copied_registry = snapshot_root / "bridge-ports.yaml"
                _copy_configuration_file(absolute(bridge_registry), copied_registry)
                PortRegistryYamlRepository(copied_registry).load()
                prepared["TSW_WINDOWS_BRIDGE_PORT_REGISTRY_PATH"] = str(copied_registry)
            except (ValueError, OSError):
                raise InstallerError(
                    "Selected bridge registry could not be safely prepared."
                ) from None
        yield prepared


def _validate_snapshot_storage(
    snapshot_root: Path, host_environment: HostEnvironmentKind
) -> None:
    """Require private Linux storage before copying any configuration bytes."""
    metadata = snapshot_root.lstat()
    filesystem = ProjectFilesystemInspector().inspect(
        str(snapshot_root),
        host_environment,
    )
    if (
        filesystem.kind
        not in {ProjectFilesystemKind.NATIVE_LINUX, ProjectFilesystemKind.WSL_LINUX}
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or metadata.st_uid != os.geteuid()
        or metadata.st_gid != os.getegid()
    ):
        raise ValueError("Configuration snapshot storage is unsafe.")


def _open_configuration_source(path: Path, *, directory: bool = False) -> int:
    """Open every path component without following symbolic links."""
    absolute = path.absolute()
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for index, component in enumerate(absolute.parts[1:]):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if directory or index < len(absolute.parts) - 2:
                flags |= os.O_DIRECTORY
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _copy_configuration_file(
    source: Path, target: Path, *, secure: bool = False
) -> None:
    descriptor = _open_configuration_source(source)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("Configuration input must be a regular file.")
        if secure and (
            metadata.st_uid != os.geteuid()
            or metadata.st_gid != os.getegid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ValueError("Operator configuration storage is unsafe.")
        with (
            os.fdopen(descriptor, "rb", closefd=False) as reader,
            target.open("xb") as writer,
        ):
            shutil.copyfileobj(reader, writer)
        target.chmod(0o600 | (stat.S_IMODE(metadata.st_mode) & 0o100))
    finally:
        os.close(descriptor)


def _copy_configuration_tree(source: Path, target: Path) -> None:
    descriptor = _open_configuration_source(source, directory=True)
    try:
        _copy_configuration_directory(descriptor, target)
    finally:
        os.close(descriptor)


def _copy_configuration_directory(descriptor: int, target: Path) -> None:
    target.mkdir(mode=0o700)
    for name in sorted(os.listdir(descriptor)):
        child = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        try:
            metadata = os.fstat(child)
            destination = target / name
            if stat.S_ISDIR(metadata.st_mode):
                _copy_configuration_directory(child, destination)
            elif stat.S_ISREG(metadata.st_mode):
                with (
                    os.fdopen(child, "rb", closefd=False) as reader,
                    destination.open("xb") as writer,
                ):
                    shutil.copyfileobj(reader, writer)
                destination.chmod(0o600 | (stat.S_IMODE(metadata.st_mode) & 0o100))
            else:
                raise ValueError(
                    "Configuration input must be a regular file or directory."
                )
        finally:
            os.close(child)


def _paths_from_env(env: Mapping[str, str], cwd: Path) -> InstallerPaths:
    def resolve(path_value: str) -> Path:
        path = Path(path_value)
        return path if path.is_absolute() else cwd / path

    return InstallerPaths(
        secret_env_file=resolve(
            env.get("TSW_INSTALL_ENV_FILE", DEFAULT_SECRET_ENV_FILE)
        ),
        native_linux_venv=resolve(
            env.get("TSW_NATIVE_LINUX_VENV", DEFAULT_NATIVE_LINUX_VENV)
        ),
    )


class ConfigurationPreparationAdapter:
    def paths(self, env: Mapping[str, str], cwd: Path) -> InstallerPaths:
        return _paths_from_env(env, cwd)

    def snapshot(
        self,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        host_runtime: HostRuntime,
    ) -> AbstractContextManager[dict[str, str]]:
        return _configuration_snapshot(options, env, cwd, host_runtime)

    def validate_read_only(
        self,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        host_runtime: HostRuntime,
    ) -> None:
        return _validate_native_installation_read_only(options, env, cwd, host_runtime)
