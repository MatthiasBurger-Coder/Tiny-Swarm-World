import re
import hashlib
from collections.abc import Mapping
from html import escape
from io import StringIO
from pathlib import Path
from typing import Any, cast

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import PortComposeFileRepository
from tiny_swarm_world.application.ports.repositories.port_effective_access_model_repository import (
    PortEffectiveAccessModelRepository,
)
from tiny_swarm_world.domain.deployment.stack_definition import (
    ComposeServiceDefinition,
    StackDefinition,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.ingress import (
    DesiredHttpsIngress,
    DesiredHttpsRoute,
    desired_https_ingress_for_profile,
)
from tiny_swarm_world.domain.network import PortRegistry, ServicePortMapping
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


STACK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
TRAEFIK_INGRESS_NETWORK_NAME = "service_access_link"
_YAML = YAML(typ="safe")


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
        self.enabled_service_names = _enabled_service_names(paths.config_root / "services.yml")
        self.logger = LoggerFactory.get_logger(self.__class__)

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        if not STACK_NAME_PATTERN.fullmatch(stack_name):
            raise ValueError("compose stack name contains invalid characters")

        for base_directory in self.base_directories:
            for compose_path in self._compose_paths_for(base_directory, stack_name):
                compose_content = compose_path.read_text(encoding="utf-8")
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
                self.logger.info("Loaded compose file for stack '%s'.", stack_name)
                return StackDefinition(
                    name=stack_name,
                    compose_content=compose_content,
                )

        raise FileNotFoundError(f"No docker-compose.yml found for stack '{stack_name}' in {self.base_directories}.")

    def get_services_of(self, stack_name: str) -> tuple[ComposeServiceDefinition, ...]:
        stack_definition = self.get_compose_of(stack_name)
        payload = _YAML.load(stack_definition.compose_content) or {}
        if not isinstance(payload, Mapping):
            return ()
        services = payload.get("services", {})
        if not isinstance(services, Mapping):
            return ()

        return tuple(
            ComposeServiceDefinition(
                name=service_name,
                published_ports=_published_ports_from_service(service_payload),
            )
            for service_name, service_payload in services.items()
            if isinstance(service_name, str) and isinstance(service_payload, Mapping)
        )

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


def _validate_swarm_stack_compose(stack_name: str, compose_content: str) -> None:
    payload = _YAML.load(compose_content) or {}
    if not isinstance(payload, Mapping):
        raise ValueError(f"compose stack '{stack_name}' must be a YAML mapping")

    services = payload.get("services")
    if not isinstance(services, Mapping) or not services:
        raise ValueError(f"compose stack '{stack_name}' must define a non-empty services mapping")

    invalid_services: list[str] = []
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str):
            invalid_services.append(str(service_name))
            continue
        if not isinstance(service_payload, Mapping):
            invalid_services.append(service_name)
            continue
        deploy = service_payload.get("deploy")
        if not isinstance(deploy, Mapping):
            invalid_services.append(service_name)

    if invalid_services:
        invalid = ", ".join(sorted(invalid_services))
        raise ValueError(f"compose stack '{stack_name}' has services without a deploy mapping: {invalid}")


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
    payload = _YAML.load(compose_content) or {}
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
    payload = _YAML.load(compose_content) or {}
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
    if isinstance(networks, list) and TRAEFIK_INGRESS_NETWORK_NAME not in networks:
        networks.append(TRAEFIK_INGRESS_NETWORK_NAME)
        network_added = True

    deploy = service_payload.setdefault("deploy", {})
    if not isinstance(deploy, dict):
        return network_added

    labels = deploy.setdefault("labels", [])
    if not isinstance(labels, list):
        return network_added

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
        for label in labels
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
    new_labels = retained_labels + rendered_labels
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
    payload = _YAML.load(compose_content) or {}
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
    dashboard_service.setdefault("environment", {})[
        "TSW_SERVICE_ACCESS_DASHBOARD_SHA256"
    ] = hashlib.sha256(dashboard_html.encode("utf-8")).hexdigest()

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
    if not services_path.is_file():
        return frozenset()
    payload = _YAML.load(services_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, Mapping):
        return frozenset()
    services = payload.get("services", {})
    if not isinstance(services, Mapping):
        return frozenset()
    return frozenset(
        service_name
        for service_name, service_payload in services.items()
        if isinstance(service_name, str)
        and isinstance(service_payload, Mapping)
        and service_payload.get("enabled") is True
    )


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
    if mapping is None or mapping.external_port is None:
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
    ("pulsar", "pulsar", 6650): "pulsar-broker",
    ("pulsar", "pulsar", 8080): "pulsar-admin-api",
    ("pulsar", "pulsar-manager", 9527): "pulsar-manager-gui",
    ("sonarqube", "sonarqube", 9000): "sonarqube-http",
    ("swagger", "swagger-ui", 8080): "swagger-ui",
    ("swagger", "swagger-nginx", 8084): "openapi-aggregator",
    ("traefik", "traefik", 80): "traefik-http",
    ("traefik", "traefik", 443): "traefik-https",
}
