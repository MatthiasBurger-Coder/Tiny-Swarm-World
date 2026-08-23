"""Operator configuration used by infrastructure composition.

This module is intentionally infrastructure-only. It translates environment
values into bounded, validated values for composition builders without leaking
environment access into the public composition facade.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunsplit

from tiny_swarm_world.infrastructure.adapters.clients.lxc_container_docker_runtime import (
    DockerAptMirrorConfiguration,
    DockerRegistryMirrorConfiguration,
)
from tiny_swarm_world.domain.artifacts import (
    DEFAULT_CONTAINER_IMAGE_CONTRACTS,
    ContainerImageContract,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    resolve_container_image_contracts,
)


DEFAULT_SETUP_SERVICE_PROFILE = ServiceStackProfile.SERVICE_ACCESS
DEFAULT_OPERATOR_CONFIGURATION_ENV_FILE = Path(
    ".tiny-swarm-world/local/live-installation.env"
)
DEFAULT_FIXED_SECRET_ENV_FILE = Path(".tiny-swarm-world/local/fixed-secrets.env")
DEFAULT_PORTAINER_API_URL = "http://localhost:10001"
_LOCAL_SERVICE_SCHEME = urlparse(DEFAULT_PORTAINER_API_URL).scheme
PORTAINER_STACK_REQUEST_TIMEOUT_ENVIRONMENT = "TSW_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS"
DEFAULT_PORTAINER_STACK_REQUEST_TIMEOUT_SECONDS = 180
SECRETS_MODE_ENVIRONMENT = "TSW_SECRETS_MODE"
FIXED_SECRET_ENV_FILE_ENVIRONMENT = "TSW_FIXED_SECRET_ENV_FILE"
SECRET_MODES = ("generated", "fixed", "infisical")
SEED_INFISICAL_ITEMS_ENVIRONMENT = "TSW_SEED_INFISICAL_ITEMS"
INFISICAL_LOGIN_EMAIL_ENVIRONMENT = "TSW_INFISICAL_LOGIN_EMAIL"
INFISICAL_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"
INFISICAL_READINESS_ATTEMPTS_ENVIRONMENT = "TSW_INFISICAL_READINESS_ATTEMPTS"
INFISICAL_READINESS_INTERVAL_ENVIRONMENT = "TSW_INFISICAL_READINESS_INTERVAL_SECONDS"
INFISICAL_URL_ENVIRONMENT = "TSW_INFISICAL_URL"
INFISICAL_INTERNAL_URL_ENVIRONMENT = "TSW_INFISICAL_INTERNAL_URL"
INFISICAL_ORGANIZATION_ENVIRONMENT = "TSW_INFISICAL_ORGANIZATION"
INFISICAL_ADMIN_FIRST_NAME_ENVIRONMENT = "TSW_INFISICAL_ADMIN_FIRST_NAME"
INFISICAL_ADMIN_LAST_NAME_ENVIRONMENT = "TSW_INFISICAL_ADMIN_LAST_NAME"
DEFAULT_INFISICAL_ORGANIZATION = "Tiny Swarm World"
DEFAULT_INFISICAL_READINESS_ATTEMPTS = 720
DEFAULT_INFISICAL_READINESS_INTERVAL_SECONDS = 5.0
DEPLOYMENT_VERIFY_TIMEOUT_ENVIRONMENT = "TSW_DEPLOYMENT_VERIFY_TIMEOUT_SECONDS"
DEFAULT_DEPLOYMENT_VERIFY_TIMEOUT_SECONDS = 300.0
SWARM_REGISTRY_ENDPOINT_ENVIRONMENT = "TSW_SWARM_REGISTRY_ENDPOINT"
DEFAULT_SWARM_REGISTRY_ENDPOINT = "127.0.0.1:13500"
WINDOWS_EXPOSURE_ENVIRONMENT = "TSW_WINDOWS_EXPOSURE"
LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT = "TSW_LXC_PROXY_LISTEN_ADDRESS"
DEFAULT_LXC_PROXY_LISTEN_ADDRESS = "0.0.0.0"
LXC_UBUNTU_APT_MIRROR_ENVIRONMENT = "TSW_LXC_UBUNTU_APT_MIRROR"
LXC_UBUNTU_SECURITY_APT_MIRROR_ENVIRONMENT = "TSW_LXC_UBUNTU_SECURITY_APT_MIRROR"
LXC_DOCKER_APT_MIRROR_ENVIRONMENT = "TSW_LXC_DOCKER_APT_MIRROR"
LXC_DOCKER_APT_GPG_URL_ENVIRONMENT = "TSW_LXC_DOCKER_APT_GPG_URL"
NEXUS_DOCKER_HUB_PROXY_REPOSITORY_ENVIRONMENT = "TSW_NEXUS_DOCKER_HUB_PROXY_REPOSITORY"
NEXUS_DOCKER_HUB_PROXY_PORT_ENVIRONMENT = "TSW_NEXUS_DOCKER_HUB_PROXY_PORT"
DEFAULT_NEXUS_DOCKER_HUB_PROXY_REPOSITORY = "docker-hub-proxy"
DEFAULT_NEXUS_DOCKER_HUB_PROXY_PORT = 5001
DEFAULT_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL = "https://registry-1.docker.io"
NEXUS_IMAGE_ENVIRONMENT = "TSW_NEXUS_IMAGE"
JENKINS_IMAGE_ENVIRONMENT = "TSW_JENKINS_IMAGE"
SERVICE_ACCESS_DASHBOARD_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_DASHBOARD_IMAGE"
SERVICE_ACCESS_NGINX_IMAGE_ENVIRONMENT = "TSW_SERVICE_ACCESS_NGINX_IMAGE"
PULSAR_IMAGE_ENVIRONMENT = "TSW_PULSAR_IMAGE"
PULSAR_MANAGER_IMAGE_ENVIRONMENT = "TSW_PULSAR_MANAGER_IMAGE"
PULSAR_MANAGER_BOOTSTRAP_IMAGE_ENVIRONMENT = "TSW_PULSAR_MANAGER_BOOTSTRAP_IMAGE"
TRAEFIK_IMAGE_ENVIRONMENT = "TSW_TRAEFIK_IMAGE"
DEFAULT_PULSAR_IMAGE = "apachepulsar/pulsar:3.0.17"
DEFAULT_PULSAR_MANAGER_IMAGE = "apachepulsar/pulsar-manager:v0.4.0"
TRAEFIK_TLS_CERT_SECRET_NAME_ENVIRONMENT = "TSW_TRAEFIK_TLS_CERT_SECRET_NAME"
TRAEFIK_TLS_KEY_SECRET_NAME_ENVIRONMENT = "TSW_TRAEFIK_TLS_KEY_SECRET_NAME"
TRAEFIK_TLS_CA_CERT_PATH_ENVIRONMENT = "TSW_TRAEFIK_CA_CERT_PATH"
TRAEFIK_TLS_CA_KEY_PATH_ENVIRONMENT = "TSW_TRAEFIK_CA_KEY_PATH"
TRAEFIK_TLS_CERT_PATH_ENVIRONMENT = "TSW_TRAEFIK_TLS_CERT_PATH"
TRAEFIK_TLS_KEY_PATH_ENVIRONMENT = "TSW_TRAEFIK_TLS_KEY_PATH"
TRAEFIK_GUI_USERS_SECRET_NAME_ENVIRONMENT = "TSW_TRAEFIK_GUI_USERS_SECRET_NAME"
TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT = "TSW_TRAEFIK_GUI_USERS_HTPASSWD"
DEFAULT_TRAEFIK_TLS_CERT_SECRET_NAME = "tsw_traefik_tls_cert"
DEFAULT_TRAEFIK_TLS_KEY_SECRET_NAME = "tsw_traefik_tls_key"
DEFAULT_TRAEFIK_GUI_USERS_SECRET_NAME = "tsw_traefik_gui_users"
INFISICAL_IMAGE_ENVIRONMENT = "TSW_INFISICAL_IMAGE"
INFISICAL_POSTGRES_IMAGE_ENVIRONMENT = "TSW_INFISICAL_POSTGRES_IMAGE"
INFISICAL_REDIS_IMAGE_ENVIRONMENT = "TSW_INFISICAL_REDIS_IMAGE"
INFISICAL_ENCRYPTION_KEY_ENVIRONMENT = "TSW_INFISICAL_ENCRYPTION_KEY"
INFISICAL_AUTH_SECRET_ENVIRONMENT = "TSW_INFISICAL_AUTH_SECRET"
INFISICAL_POSTGRES_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_POSTGRES_PASSWORD"
INFISICAL_REDIS_PASSWORD_ENVIRONMENT = "TSW_INFISICAL_REDIS_PASSWORD"
REGISTRY_ENDPOINT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?::\d{1,5})?$")


def _operator_config_value(name: str, default: str) -> str:
    return os.environ.get(name) or default


def _operator_secret_value(name: str) -> str:
    return os.environ.get(name) or f"<operator-supplied:{name}>"


def _required_operator_secret_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Required operator secret is missing: {name}")
    return value


def _operator_config_int(name: str, default: int, *, minimum: int) -> int:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value, 10)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return value


def _operator_config_float(name: str, default: float, *, minimum: float) -> float:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum:g}.")
    return value


def _secret_mode() -> str:
    mode = _operator_config_value(SECRETS_MODE_ENVIRONMENT, "generated").strip()
    if mode not in SECRET_MODES:
        raise ValueError("TSW_SECRETS_MODE must be one of generated, fixed, or infisical.")
    return mode


def _fixed_secret_env_file() -> Path:
    return Path(
        _operator_config_value(
            FIXED_SECRET_ENV_FILE_ENVIRONMENT,
            DEFAULT_FIXED_SECRET_ENV_FILE.as_posix(),
        )
    )


def _lxc_proxy_listen_address() -> str:
    address = _operator_config_value(
        LXC_PROXY_LISTEN_ADDRESS_ENVIRONMENT,
        DEFAULT_LXC_PROXY_LISTEN_ADDRESS,
    ).strip()
    if address not in {"127.0.0.1", "0.0.0.0"}:
        raise ValueError("LXC proxy listen address must be 127.0.0.1 or 0.0.0.0.")
    return address


def _lxc_docker_registry_mirror_configuration() -> DockerRegistryMirrorConfiguration | None:
    mirror_url = os.getenv("TSW_LXC_DOCKER_REGISTRY_MIRROR", "").strip()
    if not mirror_url:
        return None
    return DockerRegistryMirrorConfiguration(mirror_url)


def _lxc_docker_apt_mirror_configuration() -> DockerAptMirrorConfiguration | None:
    configuration = DockerAptMirrorConfiguration(
        ubuntu_archive_url=os.getenv(LXC_UBUNTU_APT_MIRROR_ENVIRONMENT, "").strip()
        or None,
        ubuntu_security_url=os.getenv(LXC_UBUNTU_SECURITY_APT_MIRROR_ENVIRONMENT, "").strip()
        or None,
        docker_apt_url=os.getenv(LXC_DOCKER_APT_MIRROR_ENVIRONMENT, "").strip()
        or None,
        docker_gpg_url=os.getenv(LXC_DOCKER_APT_GPG_URL_ENVIRONMENT, "").strip()
        or None,
    )
    if not configuration.configured:
        return None
    return configuration


def _operator_config_source_ref(name: str) -> str:
    return "operator_env" if os.environ.get(name) else "default"


def _add_optional_config(environment: dict[str, str], name: str) -> None:
    value = os.environ.get(name, "").strip()
    if value:
        environment[name] = value


def _container_image_contracts_from_environment() -> tuple[ContainerImageContract, ...]:
    return resolve_container_image_contracts(DEFAULT_CONTAINER_IMAGE_CONTRACTS, os.environ)


def _split_image_ref(image_ref: str) -> tuple[str, str]:
    if "@" in image_ref:
        image_name, digest = image_ref.rsplit("@", 1)
        return image_name, f"@{digest}"
    if ":" not in image_ref.rsplit("/", 1)[-1]:
        return image_ref, "latest"
    image_name, tag = image_ref.rsplit(":", 1)
    return image_name, tag


def _nexus_docker_hub_proxy_repository_name() -> str:
    repository_name = _operator_config_value(
        NEXUS_DOCKER_HUB_PROXY_REPOSITORY_ENVIRONMENT,
        DEFAULT_NEXUS_DOCKER_HUB_PROXY_REPOSITORY,
    ).strip()
    if not repository_name:
        raise ValueError("Nexus Docker Hub proxy repository name must not be empty.")
    return repository_name


def _nexus_docker_hub_proxy_port() -> int:
    raw_port = _operator_config_value(
        NEXUS_DOCKER_HUB_PROXY_PORT_ENVIRONMENT,
        str(DEFAULT_NEXUS_DOCKER_HUB_PROXY_PORT),
    ).strip()
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("Nexus Docker Hub proxy port must be an integer.") from exc
    if port <= 0 or port > 65535:
        raise ValueError("Nexus Docker Hub proxy port must be a valid TCP port.")
    return port


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _local_http_url(host: str, port: str) -> str:
    return urlunsplit((_LOCAL_SERVICE_SCHEME, f"{host}:{port}", "", "", ""))


def _nexus_docker_proxy_remote_url() -> str:
    mirror_configuration = _lxc_docker_registry_mirror_configuration()
    remote_url = (
        mirror_configuration.mirror_url
        if mirror_configuration is not None
        else DEFAULT_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL
    )
    if not _is_http_url(remote_url):
        raise ValueError("Nexus Docker proxy remote URL must be HTTP or HTTPS.")
    return remote_url


def _swarm_registry_endpoint() -> str:
    endpoint = _operator_config_value(
        SWARM_REGISTRY_ENDPOINT_ENVIRONMENT,
        DEFAULT_SWARM_REGISTRY_ENDPOINT,
    ).strip()
    if not REGISTRY_ENDPOINT_PATTERN.fullmatch(endpoint):
        raise ValueError(
            "Swarm registry endpoint must be host[:port] without scheme or credentials."
        )
    return endpoint
