"""Credentials responsibilities for the live installation boundary."""

from __future__ import annotations
from tiny_swarm_world.domain.configuration.credential_resolution import (
    CredentialResolutionError,
)
from tiny_swarm_world.application.ports.installation import (
    InstallerOptions,
    InstallerPaths,
)
from collections.abc import Mapping, Sequence
from pathlib import Path
from tiny_swarm_world.infrastructure.adapters.ingress.tls_state import (
    canonical_tls_state_root,
)
from tiny_swarm_world.domain.configuration.configuration_contract import (
    validate_traefik_htpasswd,
)
from tiny_swarm_world.domain.configuration.credential_resolution import CredentialSource
from tiny_swarm_world.application.services.credential_resolution import (
    CREDENTIAL_SOURCE_MAP_ENVIRONMENT,
    CredentialResolutionService,
    CredentialResolutionSnapshot,
    decode_source_metadata,
)
from tiny_swarm_world.application.ports.installation import (
    InstallerError,
    InstallerSecretEntry,
    TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT,
)


def _required_installer_secret_entries(
    manifest_path: Path,
) -> tuple[InstallerSecretEntry, ...]:
    from tiny_swarm_world.domain.configuration.secret_manifest import (
        SecretManifestValidationError,
    )
    from tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository import (
        SecretManifestYamlRepository,
    )

    try:
        entries = SecretManifestYamlRepository(manifest_path).load()
    except SecretManifestValidationError as error:
        raise InstallerError(f"Secret manifest is invalid: {error}") from None
    return tuple(
        InstallerSecretEntry(
            key=entry.key, source=entry.source, required=entry.required, type=entry.type
        )
        for entry in entries
        if entry.required and entry.source != "external_user_secret"
    )


def _resolve_internal_test_installer_values(
    install_env: Mapping[str, str],
    required_entries: Sequence[InstallerSecretEntry],
) -> CredentialResolutionSnapshot:
    resolution_keys = tuple(
        dict.fromkeys(
            (
                *(entry.key for entry in required_entries),
                TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT,
            )
        )
    )
    source_metadata = decode_source_metadata(
        install_env.get(CREDENTIAL_SOURCE_MAP_ENVIRONMENT)
    )
    operator_values = {
        key: (
            ""
            if source_metadata.get(key) is CredentialSource.DEFAULT
            else install_env.get(key, "")
        )
        for key in resolution_keys
    }
    return CredentialResolutionService().resolve_bootstrap(
        resolution_keys,
        operator_values=operator_values,
    )


def _ensure_default_config_exports(
    env: dict[str, str],
) -> dict[str, str]:
    from tiny_swarm_world.domain.configuration.configuration_contract import (
        missing_traefik_secret_name_defaults,
    )

    exports = missing_traefik_secret_name_defaults(env, empty_is_missing=True)
    if not env.get("TSW_LIVE_TLS_CA_BUNDLE"):
        external_ca = env.get("TSW_TRAEFIK_CA_CERT_PATH", "").strip()
        exports["TSW_LIVE_TLS_CA_BUNDLE"] = (
            external_ca or (canonical_tls_state_root(env) / "ca-bundle.pem").as_posix()
        )
    if not exports:
        return {}
    env.update(exports)
    return exports


def _require_operator_provisioned_traefik_gui_users(
    env: Mapping[str, str],
    secret_env_file: Path,
) -> None:
    if env.get(TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT, "").strip():
        try:
            validate_traefik_htpasswd(env[TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT])
        except ValueError as exc:
            raise InstallerError("Traefik htpasswd material is invalid.") from exc
        return
    raise InstallerError(
        f"Required operator secret is missing: {TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT}. "
        f"Provide complete Traefik htpasswd content in {secret_env_file.as_posix()} "
        "before starting a fresh reset."
    )


def _normalize_infisical_login_email(env: dict[str, str]) -> dict[str, str]:
    current = env.get("TSW_INFISICAL_LOGIN_EMAIL", "")
    normalized = _normalized_email_value(current)
    if not normalized or normalized == current:
        return {}
    env["TSW_INFISICAL_LOGIN_EMAIL"] = normalized
    return {"TSW_INFISICAL_LOGIN_EMAIL": normalized}


def _normalized_email_value(value: str) -> str:
    stripped = value.strip()
    quote_stripped = stripped.strip("'\"")
    if (
        quote_stripped
        and "@" in quote_stripped
        and "." in quote_stripped.partition("@")[2]
    ):
        return quote_stripped
    return stripped


class CredentialsPreparationAdapter:
    def prepare(
        self, options: InstallerOptions, env: Mapping[str, str], paths: InstallerPaths
    ) -> tuple[dict[str, str], tuple[InstallerSecretEntry, ...]]:
        install_env = dict(env)
        from tiny_swarm_world.infrastructure.adapters.repositories.installer_configuration_repository import (
            InstallerConfigurationRepository,
        )

        required_entries = _required_installer_secret_entries(
            Path(install_env["TSW_INFRA_ROOT"])
            / "config"
            / "secrets"
            / "infisical-secrets.yaml"
        )
        try:
            resolutions = _resolve_internal_test_installer_values(
                install_env,
                required_entries,
            )
        except CredentialResolutionError as error:
            raise InstallerError(str(error)) from error
        install_env.update(resolutions.values)
        install_env[CREDENTIAL_SOURCE_MAP_ENVIRONMENT] = resolutions.source_metadata()

        _normalize_infisical_login_email(install_env)
        _ensure_default_config_exports(install_env)
        _require_operator_provisioned_traefik_gui_users(
            install_env, paths.secret_env_file
        )
        install_env.setdefault("TSW_SEED_INFISICAL_ITEMS", "0")
        from tiny_swarm_world.domain.deployment import (
            service_stack_contracts_for_profile,
        )

        try:
            InstallerConfigurationRepository.validate_environment(
                install_env,
                stack_names=tuple(
                    item.stack_name
                    for item in service_stack_contracts_for_profile(
                        options.service_profile
                    )
                ),
                include_setup=True,
            )
        except ValueError:
            raise InstallerError(
                "Selected installation configuration is invalid."
            ) from None

        return install_env, required_entries
