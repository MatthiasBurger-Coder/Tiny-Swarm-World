"""Read and validate secret manifests before they enter application services."""
from pathlib import Path
from typing import cast

import yaml
from yaml.nodes import MappingNode

from tiny_swarm_world.application.ports.repositories.port_secret_manifest_repository import PortSecretManifestRepository
from tiny_swarm_world.domain.configuration.secret_manifest import (
    SecretManifestEntry,
    SecretManifestType,
    SecretManifestValidationError,
    SecretPolicy,
)

DEFAULT_MANIFEST_PATH = Path("infra/config/secrets/infisical-secrets.yaml")


class _ManifestSafeLoader(yaml.SafeLoader):
    """Preserve safe-loader scalar/merge semantics while rejecting duplicate keys."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict:
        keys: set[str] = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            if key_node.tag != "tag:yaml.org,2002:str":
                raise SecretManifestValidationError("Secret manifest field names must be strings.")
            key = str(key_node.value)
            if key in keys:
                raise SecretManifestValidationError("Duplicate YAML keys in secret manifest.")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


class SecretManifestYamlRepository(PortSecretManifestRepository):
    def __init__(self, path: Path = DEFAULT_MANIFEST_PATH) -> None:
        self.path = path

    def load(self) -> tuple[SecretManifestEntry, ...]:
        try:
            payload = yaml.load(self.path.read_text(encoding="utf-8"), Loader=_ManifestSafeLoader)
        except (OSError, UnicodeError, yaml.YAMLError):
            raise SecretManifestValidationError("Secret manifest could not be read as one valid YAML document.") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("secrets"), list):
            raise SecretManifestValidationError("Secret manifest must contain a secrets list.")
        entries = tuple(_entry(item) for item in payload["secrets"])
        if len({entry.key for entry in entries}) != len(entries):
            raise SecretManifestValidationError("Duplicate secret keys in manifest.")
        return entries


def _string(item: dict, name: str, default: str | None = None) -> str:
    value = item.get(name, default)
    if not isinstance(value, str):
        raise SecretManifestValidationError(f"Secret manifest field {name} must be a string.")
    return str(value)


def _entry(item: object) -> SecretManifestEntry:
    if not isinstance(item, dict):
        raise SecretManifestValidationError("Secret manifest entries must be mappings.")
    source = _string(item, "source")
    defaults = {
        "external_user_secret": ("operator", "external_docker_secret_or_operator_env", "operator_created_and_rotated"),
        "internal_test_catalog": ("credential_catalog", "catalog_or_operator_override", "deterministic_catalog_value_or_explicit_override"),
    }.get(source, ("unknown", "unknown", "unknown"))
    required = item.get("required", False)
    if not isinstance(required, bool):
        raise SecretManifestValidationError("Secret manifest required must be a boolean.")
    return SecretManifestEntry(
        key=_string(item, "key"),
        service=_string(item, "service", ""),
        type=cast(SecretManifestType, _string(item, "type")),
        environment=_string(item, "environment", "local"),
        description=_string(item, "description", ""),
        source=source,
        required=required,
        policy=cast(SecretPolicy, _string(item, "policy", "keep_existing")),
        owner=_string(item, "owner", defaults[0]),
        storage=_string(item, "storage", defaults[1]),
        lifecycle=_string(item, "lifecycle", defaults[2]),
    )
