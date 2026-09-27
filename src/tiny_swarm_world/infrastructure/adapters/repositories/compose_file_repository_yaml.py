from tiny_swarm_world.application.ports.repositories.port_repository_failure import RepositoryConfigurationError, RepositoryStorageError, RepositoryNotFoundError
from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure
import hashlib
import os
import re
from collections.abc import Mapping
from html import escape
from io import StringIO
from pathlib import Path
from typing import Any, cast

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scalarstring import LiteralScalarString

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import PortComposeFileRepository
from tiny_swarm_world.domain.artifacts import (
    ArtifactImageInventory,
    ArtifactImageRequirement,
    ContainerImageContract,
    DEFAULT_CONTAINER_IMAGE_CONTRACTS,
)
from tiny_swarm_world.application.ports.repositories.port_effective_access_model_repository import (
    PortEffectiveAccessModelRepository,
)
from tiny_swarm_world.domain.deployment.stack_definition import (
    ComposeServiceDefinition,
    StackDefinition,
    StackConfigurationSnapshot,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.deployment import service_stack_contracts_for_profile
from tiny_swarm_world.domain.ingress import (
    DesiredHttpsIngress,
    DesiredHttpsRoute,
    desired_https_ingress_for_profile,
)
from tiny_swarm_world.domain.network import PortRegistry, ServicePortMapping
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.adapters.configuration.configuration_sources import validate_configuration_tree
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


STACK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
TRAEFIK_INGRESS_NETWORK_NAME = "service_access_link"
_YAML = YAML(typ="safe")
IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT = {
    "nexus": "TSW_NEXUS_IMAGE",
    "jenkins": "TSW_JENKINS_IMAGE",
    "service-access-dashboard": "TSW_SERVICE_ACCESS_DASHBOARD_IMAGE",
    "service-access-nginx": "TSW_SERVICE_ACCESS_NGINX_IMAGE",
    "pulsar": "TSW_PULSAR_IMAGE",
    "pulsar-manager": "TSW_PULSAR_MANAGER_IMAGE",
    "pulsar-manager-bootstrap": "TSW_PULSAR_MANAGER_BOOTSTRAP_IMAGE",
    "infisical": "TSW_INFISICAL_IMAGE",
    "infisical-postgres": "TSW_INFISICAL_POSTGRES_IMAGE",
    "infisical-redis": "TSW_INFISICAL_REDIS_IMAGE",
    "traefik": "TSW_TRAEFIK_IMAGE",
}
_COMPOSE_IMAGE_VARIABLE_PATTERN = re.compile(
    r"^\$\{(?P<name>[A-Z][A-Z0-9_]*)(?::-?(?P<default>[^}]*))?\}$"
)


class ComposeFileRepositoryYaml(
    PortComposeFileRepository,
    PortEffectiveAccessModelRepository,
):
    def __init__(
        self,
        base_directories: list[Path] | None = None,
        port_registry: PortRegistry | None = None,
        project_paths: ProjectPaths | None = None,
        service_profile: ServiceStackProfile | str = ServiceStackProfile.SERVICE_ACCESS,
        image_contracts: tuple[ContainerImageContract, ...] | None = None,
        environment: Mapping[str, str] | None = None,
    ):
        paths = project_paths or default_project_paths()
        self.project_paths = paths
        self.base_directories = base_directories or [
            paths.infra_root / "config" / "compose",
        ]
        self.port_registry = port_registry or PortRegistryYamlRepository(
            project_paths=paths
        ).load()
        self.service_profile = ServiceStackProfile(service_profile)
        self.environment = dict(os.environ if environment is None else environment)
        self.image_contracts = resolve_container_image_contracts(
            image_contracts or DEFAULT_CONTAINER_IMAGE_CONTRACTS,
            self.environment,
        )
        self.enabled_service_names = _enabled_service_names(paths.config_root / "services.yml")
        self.logger = LoggerFactory.get_logger(self.__class__)
        self._validated_stacks: dict[str, StackDefinition] = {}
        self._validated_services: dict[str, tuple[ComposeServiceDefinition, ...]] = {}

    def validate_and_snapshot(self, stack_names: tuple[str, ...]) -> StackConfigurationSnapshot:
        definitions: dict[str, StackDefinition] = {}
        services: dict[str, tuple[ComposeServiceDefinition, ...]] = {}
        for name in dict.fromkeys(stack_names):
            definition = self.get_compose_of(name)
            definitions[name] = definition
            services[name] = self._services_from(definition)
        snapshot = StackConfigurationSnapshot(stacks=tuple(definitions.values()))
        self._validated_stacks.update(definitions)
        self._validated_services.update(services)
        return snapshot

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        try:
            return self._load_compose(stack_name)
        except OperationError:
            raise
        except OSError:
            raise RepositoryStorageError(OperationFailure.for_cause("configuration.load", "compose_repository", "filesystem_error")) from None

    def _load_compose(self, stack_name: str) -> StackDefinition:
        if stack_name in self._validated_stacks:
            return self._validated_stacks[stack_name]
        if not STACK_NAME_PATTERN.fullmatch(stack_name):
            raise RepositoryConfigurationError("compose stack name contains invalid characters")

        for base_directory in self.base_directories:
            for compose_path in self._compose_paths_for(base_directory, stack_name):
                try:
                    compose_content = compose_path.read_text(encoding="utf-8")
                except OSError:
                    raise RepositoryConfigurationError("Selected Compose configuration could not be read.", failure=OperationFailure.for_cause("configuration.load", "compose_repository", "filesystem_error")) from None
                except UnicodeError:
                    raise RepositoryConfigurationError("Selected Compose configuration could not be read.") from None
                _validate_swarm_stack_compose(stack_name, compose_content)
                compose_content = _resolve_direct_published_ports(
                    stack_name,
                    compose_content,
                    self.port_registry,
                )
                compose_content = _resolve_traefik_route_labels(
                    stack_name,
                    compose_content,
                    self._desired_routes_for_compose(),
                )
                compose_content = _resolve_service_access_dashboard_config(
                    stack_name,
                    compose_content,
                    self.render_service_access_dashboard() if stack_name == "service-access" else "",
                )
                _validate_swarm_stack_compose(stack_name, compose_content)
                self.logger.info("Loaded compose file for stack '%s'.", stack_name)
                return StackDefinition(
                    name=stack_name,
                    compose_content=compose_content,
                )

        raise RepositoryNotFoundError(OperationFailure.for_cause("configuration.load", "compose_repository", "configuration_invalid")) from None

    def get_services_of(self, stack_name: str) -> tuple[ComposeServiceDefinition, ...]:
        if stack_name in self._validated_services:
            return self._validated_services[stack_name]
        return self._services_from(self.get_compose_of(stack_name))

    def _services_from(self, definition: StackDefinition) -> tuple[ComposeServiceDefinition, ...]:
        payload = _validated_compose_payload(definition.compose_content)
        return tuple(
            ComposeServiceDefinition(
                name=service_name,
                image_ref=_effective_compose_image_ref(service_payload["image"], self.environment),
                published_ports=_published_ports_from_service(service_payload),
            )
            for service_name, service_payload in payload["services"].items()
        )

    def get_image_inventory(self) -> ArtifactImageInventory:
        requirements: list[ArtifactImageRequirement] = []
        contracts_by_ref = {contract.image_ref: contract for contract in self.image_contracts}
        for stack_contract in service_stack_contracts_for_profile(self.service_profile):
            for service in self.get_services_of(stack_contract.stack_name):
                contract = contracts_by_ref.get(service.image_ref)
                requirements.append(
                    ArtifactImageRequirement(
                        service_name=f"{stack_contract.stack_name}:{service.name}",
                        image_ref=service.image_ref,
                        build_context=contract.build_context if contract else None,
                        source=contract.source if contract else None,
                    )
                )
        selected_refs = {requirement.image_ref for requirement in requirements}
        return ArtifactImageInventory(
            profile=self.service_profile.value,
            requirements=tuple(requirements),
            contracts=tuple(
                contract
                for contract in self.image_contracts
                if contract.image_ref in selected_refs
            ),
        )

    def get_build_context_path(self, build_context: str) -> Path:
        context_paths = {
            "jenkins": self.project_paths.infra_root / "config" / "compose" / "jenkins" / "image",
            "service-access-dashboard": self.project_paths.infra_root / "config" / "compose" / "service-access" / "dashboard",
            "service-access-nginx": self.project_paths.infra_root / "config" / "compose" / "service-access" / "nginx",
        }
        try:
            return context_paths[build_context]
        except KeyError:
            raise RepositoryConfigurationError("unknown approved build context") from None

    def _compose_paths_for(self, base_directory: Path, stack_name: str) -> list[Path]:
        if not base_directory.is_dir():
            return []

        direct_path = base_directory / stack_name / "docker-compose.yml"
        if direct_path.is_file():
            return [direct_path]

        return sorted(
            compose_path
            for compose_path in base_directory.rglob("docker-compose.yml")
            if compose_path.parent.name == stack_name
        )

    def render_service_access_dashboard(self) -> str:
        return render_service_access_dashboard_html(
            self.get_effective_access_model().to_dict()
        )

    def get_effective_access_model(self) -> DesiredHttpsIngress:
        return desired_https_ingress_for_profile(
            self.service_profile,
            conditional_service_names=_conditional_route_names(
                self.port_registry,
                self.enabled_service_names,
            ),
            port_registry=self.port_registry,
        )

    def _desired_routes_for_compose(self) -> tuple[DesiredHttpsRoute, ...]:
        try:
            return self.get_effective_access_model().routes
        except ValueError as exc:
            if str(exc) == "desired HTTPS ingress requires at least one route":
                return ()
            raise


def resolve_container_image_contracts(
    contracts: tuple[ContainerImageContract, ...],
    environment: Mapping[str, str],
) -> tuple[ContainerImageContract, ...]:
    """Apply the supported image overrides used by both Compose and artifacts."""

    resolved: list[ContainerImageContract] = []
    for contract in contracts:
        environment_name = IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT.get(contract.build_context)
        image_ref = environment.get(environment_name, "").strip() if environment_name else ""
        if not image_ref:
            resolved.append(contract)
            continue
        image_name, tag = _split_image_ref(image_ref)
        resolved.append(
            ContainerImageContract(
                image_name=image_name,
                tag=tag,
                build_context=contract.build_context,
                source=contract.source,
            )
        )
    return tuple(resolved)


def _effective_compose_image_ref(value: object, environment: Mapping[str, str]) -> str:
    if not isinstance(value, str):
        return ""
    match = _COMPOSE_IMAGE_VARIABLE_PATTERN.fullmatch(value.strip())
    if match is None:
        return value.strip()
    name = match.group("name")
    configured = environment.get(name, "").strip()
    if configured:
        return configured
    return (match.group("default") or "").strip()


def _split_image_ref(image_ref: str) -> tuple[str, str]:
    if "@" in image_ref:
        image_name, digest = image_ref.rsplit("@", 1)
        return image_name, f"@{digest}"
    if ":" not in image_ref.rsplit("/", 1)[-1]:
        return image_ref, "latest"
    image_name, tag = image_ref.rsplit(":", 1)
    return image_name, tag


def _published_ports_from_service(service_payload: Mapping[object, object]) -> tuple[int, ...]:
    ports = service_payload.get("ports", ())
    if not isinstance(ports, list):
        return ()

    published_ports: list[int] = []
    for port in ports:
        published = _published_port_from_entry(port)
        if published is not None:
            published_ports.append(published)
    return tuple(dict.fromkeys(published_ports))


def _load_configuration_yaml(content: str) -> Any:
    try:
        payload = _YAML.load(content)
    except (YAMLError, RecursionError):
        raise RepositoryConfigurationError("Configuration is not a valid YAML document.") from None
    try:
        validate_configuration_tree(payload)
    except ValueError:
        raise RepositoryConfigurationError("Selected configuration contains invalid structure.") from None
    return payload


def _validate_swarm_stack_compose(stack_name: str, compose_content: str) -> None:
    _validated_compose_payload(compose_content)


def _validated_compose_payload(compose_content: str) -> dict[str, Any]:
    payload = _load_configuration_yaml(compose_content)
    if not isinstance(payload, dict):
        raise RepositoryConfigurationError("Compose stack must be a YAML mapping.")
    services = payload.get("services")
    if not isinstance(services, dict) or not services:
        raise RepositoryConfigurationError("Compose stack must define a non-empty services mapping.")
    for field in ("networks", "configs", "secrets", "volumes"):
        if field in payload:
            if not isinstance(payload[field], dict):
                raise RepositoryConfigurationError("Compose resource declarations must be mappings.")
            if not all(value is None or isinstance(value, dict) for value in payload[field].values()):
                raise RepositoryConfigurationError("Compose resource members must be mappings.")
    for name, service in services.items():
        if not name.strip() or not isinstance(service, dict):
            raise RepositoryConfigurationError("Compose services require non-empty names and mapping members.")
        if not isinstance(service.get("deploy"), dict):
            raise RepositoryConfigurationError("Compose service requires a deploy mapping.")
        image_ref = service.get("image")
        if not isinstance(image_ref, str) or not image_ref.strip():
            raise RepositoryConfigurationError("Compose service requires a non-empty image string.")
        if "ports" in service:
            if not isinstance(service["ports"], list):
                raise RepositoryConfigurationError("Compose service ports must be a list.")
            for port in service["ports"]:
                _validate_port_entry(port)
        for field in ("environment", "labels"):
            if field in service:
                _validate_scalar_collection(service[field])
        if "labels" in service["deploy"]:
            _validate_scalar_collection(service["deploy"]["labels"])
        if "networks" in service:
            networks = service["networks"]
            if isinstance(networks, list):
                if not all(isinstance(network, str) and network.strip() for network in networks):
                    raise RepositoryConfigurationError("Compose service networks must contain names.")
            elif isinstance(networks, dict):
                if not all(value is None or isinstance(value, dict) for value in networks.values()):
                    raise RepositoryConfigurationError("Compose service network options must be mappings.")
            else:
                raise RepositoryConfigurationError("Compose service networks must be a list or mapping.")
        for field in ("configs", "secrets"):
            if field in service:
                references = service[field]
                if not isinstance(references, list):
                    raise RepositoryConfigurationError("Compose resource references must be lists.")
                for reference in references:
                    source = reference.get("source") if isinstance(reference, dict) else reference
                    if not isinstance(source, str) or not source.strip():
                        raise RepositoryConfigurationError("Compose resource references require a source name.")
    return payload


def _validate_scalar_collection(value: object) -> None:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return
    if isinstance(value, dict) and all(item is None or isinstance(item, (str, int, float, bool)) for item in value.values()):
        return
    raise RepositoryConfigurationError("Compose labels and environment must be scalar mappings or string lists.")


def _validate_port_number(value: object, *, published: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise RepositoryConfigurationError("Compose port values must be integers or strings.")
    text = re.sub(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", "1", str(value))
    if not re.fullmatch(r"[0-9]+(?:-[0-9]+)?", text):
        raise RepositoryConfigurationError("Compose port values must be port numbers or ranges.")
    bounds = [int(part) for part in text.split("-")]
    if any(port < (0 if published else 1) or port > 65535 for port in bounds) or bounds[0] > bounds[-1]:
        raise RepositoryConfigurationError("Compose port values are outside the supported range.")


def _validate_port_entry(value: object) -> None:
    if isinstance(value, dict):
        _validate_port_number(value.get("target"))
        if "published" in value:
            _validate_port_number(value["published"], published=True)
        for field, allowed in (("protocol", {"tcp", "udp", "sctp"}), ("mode", {"host", "ingress"})):
            if field in value and (not isinstance(value[field], str) or (value[field] not in allowed and not re.fullmatch(r"\$\{[^}]+\}", value[field]))):
                raise RepositoryConfigurationError("Compose port protocol or mode is invalid.")
        if "host_ip" in value and not isinstance(value["host_ip"], str):
            raise RepositoryConfigurationError("Compose port host address must be a string.")
        return
    if isinstance(value, int) and not isinstance(value, bool):
        _validate_port_number(value)
        return
    if not isinstance(value, str):
        raise RepositoryConfigurationError("Compose port entries must use supported short or long syntax.")
    normalized = re.sub(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", "1", value)
    if "/" in normalized:
        normalized, protocol = normalized.rsplit("/", 1)
        if protocol not in {"tcp", "udp", "sctp"}:
            raise RepositoryConfigurationError("Compose port protocol is invalid.")
    if normalized.startswith("["):
        if "]:" not in normalized:
            raise RepositoryConfigurationError("Compose port host address is invalid.")
        normalized = normalized.split("]:", 1)[1]
    parts = normalized.split(":")
    if len(parts) == 3:
        if not parts[0]:
            raise RepositoryConfigurationError("Compose port host address must not be empty.")
        parts = parts[1:]
    if len(parts) not in {1, 2}:
        raise RepositoryConfigurationError("Compose port short syntax is invalid.")
    _validate_port_number(parts[-1])
    if len(parts) == 2:
        _validate_port_number(parts[0], published=True)


def _published_port_from_entry(port_entry: object) -> int | None:
    if isinstance(port_entry, Mapping):
        return _published_port_from_value(port_entry.get("published"))
    if isinstance(port_entry, str):
        return _published_port_from_short_syntax(port_entry)
    return None


def _published_port_from_value(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _published_port_from_short_syntax(value: str) -> int | None:
    port_without_protocol = value.rsplit("/", 1)[0]
    if ":" not in port_without_protocol:
        return None
    host_side = port_without_protocol.rsplit(":", 1)[0]
    if host_side.startswith("[") and "]:" in host_side:
        host_side = host_side.rsplit("]:", 1)[1]
    elif ":" in host_side:
        host_side = host_side.rsplit(":", 1)[1]
    if "-" in host_side:
        host_side = host_side.split("-", 1)[0]
    return int(host_side) if host_side.isdigit() else None


def _resolve_direct_published_ports(
    stack_name: str,
    compose_content: str,
    port_registry: PortRegistry,
) -> str:
    payload = _load_configuration_yaml(compose_content)
    if not isinstance(payload, Mapping):
        return compose_content
    services = payload.get("services")
    if not isinstance(services, Mapping):
        return compose_content

    ports_by_id = {mapping.port_id: mapping for mapping in port_registry.mappings}
    mutated = _apply_direct_published_ports(stack_name, services, ports_by_id)
    if not mutated:
        return compose_content

    return _dump_yaml_payload(payload)


def _resolve_traefik_route_labels(
    _stack_name: str,
    compose_content: str,
    routes: tuple[DesiredHttpsRoute, ...],
) -> str:
    payload = _load_configuration_yaml(compose_content)
    if not isinstance(payload, Mapping):
        return compose_content
    services = payload.get("services")
    if not isinstance(services, Mapping):
        return compose_content

    routes_by_upstream = _routes_by_upstream(routes)
    mutated = False
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str):
            continue
        service_routes = tuple(routes_by_upstream.get(service_name, ()))
        if _apply_traefik_labels(service_payload, service_routes):
            mutated = True

    if not mutated:
        return compose_content
    mutable_payload = cast(dict[str, Any], payload)
    if TRAEFIK_INGRESS_NETWORK_NAME not in mutable_payload.get("networks", {}):
        networks = mutable_payload.setdefault("networks", {})
        if isinstance(networks, dict):
            networks[TRAEFIK_INGRESS_NETWORK_NAME] = {
                "name": TRAEFIK_INGRESS_NETWORK_NAME,
                "external": True,
            }
    return _dump_yaml_payload(payload)


def _routes_by_upstream(
    routes: tuple[DesiredHttpsRoute, ...],
) -> dict[str, tuple[DesiredHttpsRoute, ...]]:
    mapped_routes: dict[str, list[DesiredHttpsRoute]] = {}
    for route in routes:
        mapped_routes.setdefault(route.upstream_service, []).append(route)
    return {key: tuple(value) for key, value in mapped_routes.items()}


def _apply_traefik_labels(
    service_payload: object,
    service_routes: tuple[DesiredHttpsRoute, ...],
) -> bool:
    if not isinstance(service_payload, dict) or not service_routes:
        return False

    networks = service_payload.setdefault("networks", [])
    network_added = False
    if TRAEFIK_INGRESS_NETWORK_NAME not in networks:
        if isinstance(networks, list):
            networks.append(TRAEFIK_INGRESS_NETWORK_NAME)
        elif isinstance(networks, dict):
            networks[TRAEFIK_INGRESS_NETWORK_NAME] = None
        network_added = True

    deploy = service_payload.setdefault("deploy", {})
    if not isinstance(deploy, dict):
        return network_added

    labels = deploy.setdefault("labels", [])
    label_items = (
        [f"{key}={value}" for key, value in labels.items()]
        if isinstance(labels, dict) else labels
    )

    router_names = tuple(_router_name_for(route) for route in service_routes)
    rendered_labels = list(
        dict.fromkeys(
            label
            for route, router_name in zip(service_routes, router_names, strict=True)
            for label in _traefik_labels_for_route(route, router_name)
        )
    )
    retained_labels = [
        label
        for label in label_items
        if not (
            isinstance(label, str)
            and (
                label.startswith("traefik.enable=")
                or label.startswith("traefik.swarm.network=")
                or any(
                    label.startswith(
                        (
                            f"traefik.http.routers.{router_name}.",
                            f"traefik.http.services.{router_name}.",
                        )
                    )
                    for router_name in router_names
                )
            )
        )
    ]
    new_labels: list[str] | dict[str, object] = retained_labels + rendered_labels
    if isinstance(labels, dict):
        retained_keys = {label.split("=", 1)[0] for label in retained_labels}
        new_labels = {key: value for key, value in labels.items() if key in retained_keys}
        new_labels.update(dict(label.split("=", 1) for label in rendered_labels))
    if labels != new_labels:
        deploy["labels"] = new_labels
        return True
    return network_added


def _resolve_service_access_dashboard_config(
    stack_name: str,
    compose_content: str,
    dashboard_html: str,
) -> str:
    if stack_name != "service-access":
        return compose_content
    payload = _load_configuration_yaml(compose_content)
    if not isinstance(payload, Mapping):
        return compose_content
    services = payload.get("services")
    if not isinstance(services, Mapping):
        return compose_content
    dashboard_service = services.get("service-access-dashboard")
    if not isinstance(dashboard_service, dict):
        return compose_content

    mutable_payload = cast(dict[str, Any], payload)
    configs = cast(dict[str, Any], mutable_payload.setdefault("configs", {}))
    configs["service_access_dashboard_index"] = {
        "file": "${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}"
        "/service-access/dashboard/index.html",
    }
    dashboard_service["configs"] = [
        {
            "source": "service_access_dashboard_index",
            "target": "/usr/share/nginx/html/index.html",
        }
    ]
    environment = dashboard_service.setdefault("environment", {})
    digest_key = "TSW_SERVICE_ACCESS_DASHBOARD_SHA256"
    digest = hashlib.sha256(dashboard_html.encode("utf-8")).hexdigest()
    if isinstance(environment, list):
        dashboard_service["environment"] = [
            value for value in environment if value.split("=", 1)[0] != digest_key
        ] + [f"{digest_key}={digest}"]
    else:
        environment[digest_key] = digest

    return _dump_yaml_payload(payload)


def _dump_yaml_payload(payload: object) -> str:
    _preserve_multiline_strings(payload)
    sink = StringIO()
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.width = 4096
    yaml.dump(payload, sink)
    return sink.getvalue()


def _preserve_multiline_strings(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str) and "\n" in item:
                value[key] = LiteralScalarString(item)
            else:
                _preserve_multiline_strings(item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, str) and "\n" in item:
                value[index] = LiteralScalarString(item)
            else:
                _preserve_multiline_strings(item)


def _traefik_labels_for_route(route: DesiredHttpsRoute, router_name: str) -> list[str]:
    return [
        "traefik.enable=true",
        f"traefik.swarm.network={TRAEFIK_INGRESS_NETWORK_NAME}",
        f"traefik.http.routers.{router_name}.rule=Host(`{route.hostname}`)",
        f"traefik.http.routers.{router_name}.entrypoints=websecure",
        f"traefik.http.routers.{router_name}.tls=true",
        f"traefik.http.routers.{router_name}.service={router_name}",
        (
            f"traefik.http.services.{router_name}"
            f".loadbalancer.server.port={route.upstream_port}"
        ),
    ]


def _router_name_for(route: DesiredHttpsRoute) -> str:
    return route.hostname.split(".", maxsplit=1)[0]


def _enabled_service_names(services_path: Path) -> frozenset[str]:
    try:
        return _parse_enabled_service_names(services_path)
    except OperationError:
        raise
    except OSError:
        raise RepositoryStorageError(OperationFailure.for_cause("configuration.load", "compose_repository", "filesystem_error")) from None


def _parse_enabled_service_names(services_path: Path) -> frozenset[str]:
    if not services_path.exists():
        return frozenset()
    try:
        payload = _load_configuration_yaml(services_path.read_text(encoding="utf-8"))
    except OSError:
        raise RepositoryConfigurationError("Service catalogue could not be read.", failure=OperationFailure.for_cause("configuration.load", "compose_repository", "filesystem_error")) from None
    except UnicodeError:
        raise RepositoryConfigurationError("Service catalogue could not be read.") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("services"), dict):
        raise RepositoryConfigurationError("Service catalogue must contain a services mapping.")
    enabled: set[str] = set()
    for name, service in payload["services"].items():
        if not name.strip() or not isinstance(service, dict):
            raise RepositoryConfigurationError("Service catalogue entries require names and mappings.")
        value = service.get("enabled", False)
        if not isinstance(value, bool):
            raise RepositoryConfigurationError("Service catalogue enabled must be a boolean.")
        if value:
            enabled.add(str(name))
    return frozenset(enabled)


def _conditional_route_names(
    port_registry: PortRegistry,
    enabled_service_names: frozenset[str],
) -> tuple[str, ...]:
    route_names: list[str] = []
    for mapping in port_registry.mappings:
        if not mapping.route_host:
            continue
        route_name = _route_name_for_port_mapping(mapping)
        if route_name in {"api", "app", "grafana", "prometheus"} and (
            route_name in enabled_service_names or mapping.service_id in enabled_service_names
        ):
            route_names.append(route_name)
    return tuple(dict.fromkeys(route_names))


def _route_name_for_port_mapping(mapping: ServicePortMapping) -> str:
    if mapping.port_id == "tiny-swarm-frontend":
        return "app"
    if mapping.port_id == "tiny-swarm-backend":
        return "api"
    if mapping.port_id.endswith("-http"):
        return mapping.port_id.removesuffix("-http")
    return mapping.port_id


def render_service_access_dashboard_html(effective_access_model: Mapping[str, object]) -> str:
    links = cast(list[Mapping[str, object]], effective_access_model.get("service_access_links", []))
    rows = "\n".join(_dashboard_row(link) for link in links)
    service_count = len(links)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>Tiny Swarm World Service Access</title>
  <style>
    :root {{ color-scheme: light; --bg: #f5f7fa; --panel: #ffffff; --line: #d7dde6; --ink: #172033; --muted: #657386; --accent: #146b7f; --accent-soft: #e8f6f8; --warn: #7a5200; --warn-bg: #fff8e8; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 28px 0; }}
    header {{ display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 14px; margin-bottom: 18px; }}
    h1 {{ margin: 0 0 6px; font-size: 2rem; line-height: 1.1; font-weight: 760; letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.5; }}
    a {{ color: var(--accent); font-weight: 650; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .vault-link {{ display: inline-flex; align-items: center; justify-content: center; min-height: 40px; padding: 0 14px; border: 1px solid var(--accent); border-radius: 6px; background: var(--accent-soft); color: #0d5364; white-space: nowrap; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }}
    .chip {{ display: inline-flex; align-items: center; min-height: 30px; padding: 0 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--panel); color: var(--muted); font-size: 0.86rem; font-weight: 650; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }}
    table {{ width: 100%; min-width: 820px; border-collapse: collapse; }}
    th, td {{ padding: 13px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; line-height: 1.45; }}
    th {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; font-weight: 760; }}
    tbody tr:last-child th, tbody tr:last-child td {{ border-bottom: 0; }}
    tbody th {{ width: 170px; color: var(--ink); font-size: 0.98rem; text-transform: none; }}
    code {{ padding: 2px 5px; border-radius: 4px; background: #eef1f5; color: #1e293b; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: 0.9em; }}
    .pwd {{ display: grid; gap: 4px; }}
    .pwd small {{ color: var(--muted); font-size: 0.82rem; }}
    .note {{ margin-top: 14px; padding: 14px 16px; border-left: 4px solid var(--warn); background: var(--warn-bg); color: #3c2d12; border-radius: 4px; }}
    @media (max-width: 720px) {{ main {{ width: min(100vw - 20px, 1180px); padding: 20px 0; }} header {{ align-items: flex-start; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Service Access</h1>
        <p>Management table for local Tiny Swarm World services and Infisical secret entries.</p>
      </div>
      <a class="vault-link" href="https://infisical.tsw.local" target="_blank" rel="noopener noreferrer">Open Infisical</a>
    </header>
    <div class="toolbar" aria-label="Access summary">
      <span class="chip">{service_count} services</span>
      <span class="chip">Passwords are visible through Infisical</span>
      <span class="chip">Traefik routed access</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th scope="col">Service</th><th scope="col">URL</th><th scope="col">User</th><th scope="col">Password</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
    <p class="note">This page does not store plaintext passwords. The <strong>Password</strong> column shows the Infisical entry or marks services that do not require a login. Password values are only viewed and copied in Infisical.</p>
  </main>
</body>
</html>
"""


def _dashboard_row(link: Mapping[str, object]) -> str:
    service = str(link["service"])
    url = str(link["url"])
    user, password_html = _dashboard_credentials_for(link)
    return (
        f'          <tr><th scope="row">{escape(service)}</th>'
        f'<td><a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(url)}</a></td>'
        f"<td><code>{escape(user)}</code></td><td>{password_html}</td></tr>"
    )


def _dashboard_credentials_for(link: Mapping[str, object]) -> tuple[str, str]:
    credential = link.get("credential")
    if not isinstance(credential, Mapping):
        note = str(link.get("no_login_note") or "Login is not required")
        return (
            "none",
            f'<span class="pwd"><code>not required</code><small>{escape(note)}</small></span>',
        )
    user = str(credential["username_label"])
    item = str(credential["item_reference"])
    note = str(credential["note"])
    return (
        user,
        (
            '<span class="pwd"><a href="https://infisical.tsw.local" target="_blank" '
            f'rel="noopener noreferrer"><code>{escape(item)}</code></a><small>{escape(note)}</small></span>'
        ),
    )


def _apply_direct_published_ports(
    stack_name: str,
    services: Mapping[object, object],
    ports_by_id: Mapping[str, ServicePortMapping],
) -> bool:
    mutated = False
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str) or not isinstance(service_payload, Mapping):
            continue
        configured_ports = service_payload.get("ports")
        if not isinstance(configured_ports, list):
            continue

        for entry in configured_ports:
            mutated = _apply_direct_published_port(
                stack_name,
                service_name,
                entry,
                ports_by_id,
            ) or mutated
    return mutated


def _apply_direct_published_port(
    stack_name: str,
    service_name: str,
    entry: object,
    ports_by_id: Mapping[str, ServicePortMapping],
) -> bool:
    if not isinstance(entry, dict):
        return False
    port_id = _port_id_for_entry(stack_name, service_name, entry)
    if port_id is None:
        return False
    mapping = ports_by_id.get(port_id)
    if mapping is None:
        raise RepositoryConfigurationError(f"direct port '{port_id}' is missing from the port registry")
    if mapping.external_port is None:
        return False
    if entry.get("published") == mapping.external_port:
        return False
    entry["published"] = mapping.external_port
    return True


def _port_id_for_entry(
    stack_name: str,
    service_name: str,
    port_entry: Mapping[object, object],
) -> str | None:
    target = port_entry.get("target")
    if not isinstance(target, int):
        return None
    return _DIRECT_PUBLISHED_PORT_IDS.get((stack_name, service_name, target))


_DIRECT_PUBLISHED_PORT_IDS: dict[tuple[str, str, int], str] = {
    ("portainer", "portainer", 9000): "portainer-http",
    ("jenkins", "jenkins", 8080): "jenkins-http",
    ("jenkins", "jenkins", 50000): "jenkins-agent",
    ("nexus", "nexus", 8081): "nexus-http",
    ("nexus", "nexus", 5000): "nexus-docker-http",
    ("nexus", "nexus", 5001): "nexus-docker-https",
    ("infisical", "infisical", 8080): "infisical-http",
    ("service-access", "service-access-nginx", 80): "service-access-http",
    ("pulsar", "pulsar", 6650): "pulsar-broker",
    ("pulsar", "pulsar", 8080): "pulsar-admin-api",
    ("pulsar", "pulsar-manager", 9527): "pulsar-manager-gui",
    ("sonarqube", "sonarqube", 9000): "sonarqube-http",
    ("swagger", "swagger-ui", 8080): "swagger-ui",
    ("swagger", "swagger-nginx", 8084): "openapi-aggregator",
    ("traefik", "traefik", 80): "traefik-http",
    ("traefik", "traefik", 443): "traefik-https",
}
