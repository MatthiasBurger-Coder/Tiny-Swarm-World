from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from urllib.parse import urlparse


CONFIG_KEY_PATTERN = re.compile(r"^TSW_[A-Z0-9_]+$")
SECRET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]*$")
IMAGE_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]*$")
WINDOWS_PATH_PATTERN = re.compile(r"^[A-Za-z]:\\")
BOOLEAN_VALUES = frozenset({"0", "1", "false", "true"})


class ConfigurationValueKind(str, Enum):
    SECRET_VALUE = "secret_value"
    SECRET_NAME = "secret_name"
    URL = "url"
    POSITIVE_INTEGER = "positive_integer"
    BOOLEAN_FLAG = "boolean_flag"
    IMAGE_REFERENCE = "image_reference"
    IDENTIFIER = "identifier"
    TEXT = "text"
    LOCAL_PATH = "local_path"
    NODE_PATH = "node_path"


class ConfigurationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ConfigurationRequirement:
    key: str
    scope: str
    value_kind: ConfigurationValueKind
    required: bool
    description: str
    default: str = ""

    def __post_init__(self) -> None:
        if not CONFIG_KEY_PATTERN.fullmatch(self.key):
            raise ValueError("configuration key must be a TSW_* identifier")
        if not self.scope:
            raise ValueError("configuration scope must not be empty")
        if not self.description:
            raise ValueError("configuration description must not be empty")
        if self.default and self.value_kind is ConfigurationValueKind.SECRET_VALUE:
            raise ValueError("secret value requirements must not define committed defaults")
        if self.default:
            _validate_value(self.default, self.value_kind)

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "scope": self.scope,
            "value_kind": self.value_kind.value,
            "required": self.required,
            "default": "<redacted>" if self.value_kind is ConfigurationValueKind.SECRET_VALUE else self.default,
            "description": self.description,
        }


@dataclass(frozen=True)
class ConfigurationFinding:
    key: str
    status: ConfigurationStatus
    message: str
    remediation: str
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))

    @property
    def passed(self) -> bool:
        return self.status == ConfigurationStatus.PASSED

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "status": self.status.value,
            "message": self.message,
            "remediation": self.remediation,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class ConfigurationValidationResult:
    findings: tuple[ConfigurationFinding, ...]

    @property
    def passed(self) -> bool:
        return all(finding.passed for finding in self.findings)

    @property
    def failed_findings(self) -> tuple[ConfigurationFinding, ...]:
        return tuple(finding for finding in self.findings if not finding.passed)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": ConfigurationStatus.PASSED.value if self.passed else ConfigurationStatus.FAILED.value,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class ConfigurationContract:
    schema_version: str
    requirements: tuple[ConfigurationRequirement, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "1":
            raise ValueError("unsupported configuration contract schema version")
        keys = [requirement.key for requirement in self.requirements]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"duplicate configuration requirements: {duplicates}")
        object.__setattr__(self, "requirements", tuple(self.requirements))

    def validate(self, values: Mapping[str, str]) -> ConfigurationValidationResult:
        findings = tuple(_finding_for_requirement(requirement, values) for requirement in self.requirements)
        return ConfigurationValidationResult(findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "requirements": [requirement.to_dict() for requirement in self.requirements],
        }


def default_configuration_contract() -> ConfigurationContract:
    return ConfigurationContract(
        schema_version="1",
        requirements=(
            _required_secret("TSW_PORTAINER_ADMIN_PASSWORD", "portainer", "Portainer admin password."),
            _required_secret("TSW_NEXUS_ADMIN_PASSWORD", "nexus", "Nexus admin password."),
            _required_secret("TSW_JENKINS_ADMIN_PASSWORD", "jenkins", "Jenkins admin password."),
            _required_secret("TSW_SONARQUBE_ADMIN_PASSWORD", "sonarqube", "SonarQube admin password."),
            _required_secret("TSW_POSTGRES_PASSWORD", "sonarqube", "SonarQube PostgreSQL password."),
            _required_secret(
                "TSW_SONARQUBE_POSTGRES_PASSWORD",
                "sonarqube",
                "SonarQube PostgreSQL service password.",
            ),
            ConfigurationRequirement(
                key="TSW_INFISICAL_LOGIN_EMAIL",
                scope="infisical",
                value_kind=ConfigurationValueKind.TEXT,
                required=True,
                description="Infisical bootstrap login email.",
            ),
            _required_secret(
                "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD",
                "infisical",
                "Infisical bootstrap admin password.",
            ),
            _required_secret("TSW_INFISICAL_ENCRYPTION_KEY", "infisical", "Infisical encryption key."),
            _required_secret("TSW_INFISICAL_AUTH_SECRET", "infisical", "Infisical auth secret."),
            _required_secret(
                "TSW_INFISICAL_POSTGRES_PASSWORD",
                "infisical",
                "Infisical PostgreSQL password.",
            ),
            _required_secret("TSW_INFISICAL_REDIS_PASSWORD", "infisical", "Infisical Redis password."),
            ConfigurationRequirement(
                key="TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS",
                scope="deployment",
                value_kind=ConfigurationValueKind.POSITIVE_INTEGER,
                required=False,
                default="180",
                description="Portainer stack request timeout in seconds.",
            ),
            ConfigurationRequirement(
                key="TSW_SEED_INFISICAL_ITEMS",
                scope="deployment",
                value_kind=ConfigurationValueKind.BOOLEAN_FLAG,
                required=False,
                default="0",
                description="Controls optional legacy Infisical inventory seeding.",
            ),
            ConfigurationRequirement(
                key="TSW_LXC_DOCKER_REGISTRY_MIRROR",
                scope="platform",
                value_kind=ConfigurationValueKind.URL,
                required=False,
                description="Docker registry mirror URL reachable from managed LXC nodes.",
            ),
            ConfigurationRequirement(
                key="TSW_PULSAR_ADMIN_URL",
                scope="pulsar",
                value_kind=ConfigurationValueKind.URL,
                required=False,
                description="Internal Pulsar Admin API URL for local standalone mode.",
            ),
            ConfigurationRequirement(
                key="TSW_PULSAR_PUBLIC_ADMIN_URL",
                scope="pulsar",
                value_kind=ConfigurationValueKind.URL,
                required=False,
                description="Host-accessible Pulsar Admin API URL for browser/live checks.",
            ),
            ConfigurationRequirement(
                key="TSW_TRAEFIK_TLS_CERT_SECRET_NAME",
                scope="traefik",
                value_kind=ConfigurationValueKind.SECRET_NAME,
                required=False,
                default="tsw_traefik_tls_cert",
                description="External Docker secret name for Traefik TLS certificate material.",
            ),
            ConfigurationRequirement(
                key="TSW_TRAEFIK_TLS_KEY_SECRET_NAME",
                scope="traefik",
                value_kind=ConfigurationValueKind.SECRET_NAME,
                required=False,
                default="tsw_traefik_tls_key",
                description="External Docker secret name for Traefik TLS private key material.",
            ),
        ),
    )


def _required_secret(key: str, scope: str, description: str) -> ConfigurationRequirement:
    return ConfigurationRequirement(
        key=key,
        scope=scope,
        value_kind=ConfigurationValueKind.SECRET_VALUE,
        required=True,
        description=description,
    )


def _finding_for_requirement(
    requirement: ConfigurationRequirement,
    values: Mapping[str, str],
) -> ConfigurationFinding:
    supplied_value = values.get(requirement.key, "")
    value = supplied_value or requirement.default
    source = "missing"
    if supplied_value:
        source = "environment"
    elif requirement.default:
        source = "default"
    evidence = {
        "key": requirement.key,
        "scope": requirement.scope,
        "value_kind": requirement.value_kind.value,
        "required": str(requirement.required).lower(),
        "source": source,
    }
    if not value:
        if requirement.required:
            return ConfigurationFinding(
                key=requirement.key,
                status=ConfigurationStatus.FAILED,
                message="Required configuration value is missing.",
                remediation=f"Provide {requirement.key} through an operator-owned environment source.",
                evidence=evidence,
            )
        return ConfigurationFinding(
            key=requirement.key,
            status=ConfigurationStatus.PASSED,
            message="Optional configuration value is not set.",
            remediation="None.",
            evidence=evidence,
        )
    try:
        _validate_value(value, requirement.value_kind)
    except ValueError as exc:
        return ConfigurationFinding(
            key=requirement.key,
            status=ConfigurationStatus.FAILED,
            message=str(exc),
            remediation=f"Provide a valid {requirement.value_kind.value} for {requirement.key}.",
            evidence=evidence,
        )
    return ConfigurationFinding(
        key=requirement.key,
        status=ConfigurationStatus.PASSED,
        message="Configuration value satisfies the typed contract.",
        remediation="None.",
        evidence=evidence,
    )


def _validate_value(value: str, value_kind: ConfigurationValueKind) -> None:
    if not value:
        raise ValueError("configuration value must not be empty")
    if value_kind is ConfigurationValueKind.SECRET_VALUE:
        return
    if value_kind is ConfigurationValueKind.SECRET_NAME:
        _validate_secret_name(value)
        return
    if value_kind is ConfigurationValueKind.URL:
        _validate_url(value)
        return
    if value_kind is ConfigurationValueKind.POSITIVE_INTEGER:
        _validate_positive_integer(value)
        return
    if value_kind is ConfigurationValueKind.BOOLEAN_FLAG:
        _validate_boolean_flag(value)
        return
    if value_kind is ConfigurationValueKind.IMAGE_REFERENCE:
        _validate_image_reference(value)
        return
    if value_kind is ConfigurationValueKind.IDENTIFIER:
        _validate_identifier(value)
        return
    if value_kind is ConfigurationValueKind.LOCAL_PATH:
        _validate_local_path(value)
        return
    if value_kind is ConfigurationValueKind.NODE_PATH:
        _validate_node_path(value)


def _validate_secret_name(value: str) -> None:
    if not SECRET_NAME_PATTERN.fullmatch(value):
        raise ValueError("secret name must be a safe Docker secret identifier")


def _validate_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use http or https and include a host")
    if parsed.username or parsed.password:
        raise ValueError("URL must not include credentials")


def _validate_positive_integer(value: str) -> None:
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise ValueError("value must be a positive integer") from exc
    if parsed < 1:
        raise ValueError("value must be a positive integer")


def _validate_boolean_flag(value: str) -> None:
    if value.casefold() not in BOOLEAN_VALUES:
        raise ValueError("boolean flag must be one of 0, 1, true, or false")


def _validate_image_reference(value: str) -> None:
    if any(character.isspace() for character in value) or "://" in value:
        raise ValueError("image reference must not contain whitespace or URL syntax")
    if not IMAGE_REFERENCE_PATTERN.fullmatch(value):
        raise ValueError("image reference contains invalid characters")


def _validate_identifier(value: str) -> None:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError("identifier contains invalid characters")


def _validate_local_path(value: str) -> None:
    if WINDOWS_PATH_PATTERN.search(value) or "\\" in value:
        raise ValueError("local paths must use Linux/WSL path syntax")


def _validate_node_path(value: str) -> None:
    _validate_local_path(value)
    if not value.startswith("/"):
        raise ValueError("managed-node paths must be absolute POSIX paths")
