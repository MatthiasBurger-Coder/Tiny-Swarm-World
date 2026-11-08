from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from ruamel.yaml import YAML

from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


CORE_ROUTE_EXPECTATIONS: Mapping[str, tuple[str, str, int]] = {
    "portainer": ("portainer.tsw.local", "portainer", 9000),
    "nexus": ("nexus.tsw.local", "nexus", 8081),
    "jenkins": ("jenkins.tsw.local", "jenkins", 8080),
    "pulsar-admin-api": ("pulsar-api.tsw.local", "pulsar", 8080),
    "pulsar-manager": ("pulsar.tsw.local", "pulsar-manager", 9527),
    "sonarqube": ("sonarqube.tsw.local", "sonarqube", 9000),
    "swagger": ("swagger.tsw.local", "swagger-nginx", 8084),
    "infisical": ("infisical.tsw.local", "infisical", 8080),
    "service-access": (
        "service-access.tsw.local",
        "service-access-dashboard",
        80,
    ),
}

OPTIONAL_ROUTE_EXPECTATIONS: Mapping[str, tuple[str, str, str, int]] = {
    "prometheus": ("prometheus", "prometheus.tsw.local", "prometheus", 9090),
    "grafana": ("grafana", "grafana.tsw.local", "grafana", 3000),
    "app": ("tiny-swarm", "app.tsw.local", "tiny-swarm", 8080),
    "api": ("tiny-swarm", "api.tsw.local", "tiny-swarm", 8081),
}

_CORE_ENABLED_SERVICES = (
    "portainer",
    "nexus",
    "jenkins",
    "pulsar",
    "sonarqube",
    "swagger",
    "infisical",
    "service-access",
    "traefik",
)

_STACK_SERVICES: Mapping[str, tuple[str, ...]] = {
    "portainer": ("portainer",),
    "nexus": ("nexus",),
    "jenkins": ("jenkins",),
    "pulsar": ("pulsar", "pulsar-manager"),
    "sonarqube": ("sonarqube",),
    "swagger": ("swagger-nginx",),
    "infisical": ("infisical",),
    "service-access": ("service-access-dashboard",),
    "prometheus": ("prometheus",),
    "grafana": ("grafana",),
    "tiny-swarm": ("tiny-swarm",),
}


@dataclass(frozen=True)
class EffectiveAccessModelFixture:
    root: Path
    project_paths: ProjectPaths
    repository: ComposeFileRepositoryYaml


@contextmanager
def effective_access_model_fixture(
    *,
    enabled_services: Sequence[str] = (),
) -> Iterator[EffectiveAccessModelFixture]:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        project_paths = ProjectPaths.from_roots(root)
        compose_root = project_paths.config_root / "compose"
        _write_yaml(
            project_paths.config_root / "services.yml",
            {
                "services": {
                    service_name: {"enabled": True}
                    for service_name in dict.fromkeys(
                        (*_CORE_ENABLED_SERVICES, *enabled_services)
                    )
                }
            },
        )
        _write_yaml(
            project_paths.config_root / "ports.yaml",
            {"ranges": [], "ports": _route_port_fixtures()},
        )
        for stack_name, service_names in _STACK_SERVICES.items():
            _write_yaml(
                compose_root / stack_name / "docker-compose.yml",
                {
                    "services": {
                        service_name: {
                            "image": "example.invalid/tiny-swarm-world/test:latest",
                            "deploy": {},
                        }
                        for service_name in service_names
                    }
                },
            )
        yield EffectiveAccessModelFixture(
            root=root,
            project_paths=project_paths,
            repository=ComposeFileRepositoryYaml(
                base_directories=[compose_root],
                project_paths=project_paths,
            ),
        )


def _route_port_fixtures() -> list[dict[str, Any]]:
    return [
        _port("api-gateway-http", "api-gateway", 80, 10080),
        _port("api-gateway-https", "api-gateway", 443, 10443),
        _route_port("portainer-http", "portainer", 9000, 10001, "portainer.tsw.local"),
        _route_port("nexus-http", "nexus", 8081, 13081, "nexus.tsw.local"),
        _route_port("jenkins-http", "jenkins", 8080, 11080, "jenkins.tsw.local"),
        _route_port(
            "pulsar-admin-api",
            "pulsar",
            8080,
            14080,
            "pulsar-api.tsw.local",
            route_name="pulsar-admin-api",
            upstream_service="pulsar",
            health_path="/admin/v2/clusters",
        ),
        _route_port(
            "pulsar-manager-gui",
            "pulsar",
            9527,
            14081,
            "pulsar.tsw.local",
            route_name="pulsar-manager",
            upstream_service="pulsar-manager",
        ),
        _route_port(
            "sonarqube-http",
            "sonarqube",
            9000,
            12000,
            "sonarqube.tsw.local",
        ),
        _route_port(
            "openapi-aggregator",
            "swagger",
            8084,
            16081,
            "swagger.tsw.local",
            route_name="swagger",
            upstream_service="swagger-nginx",
        ),
        _route_port(
            "infisical-http",
            "infisical",
            8080,
            17080,
            "infisical.tsw.local",
        ),
        _route_port(
            "service-access-http",
            "service-access",
            80,
            10000,
            "service-access.tsw.local",
            upstream_service="service-access-dashboard",
        ),
        _route_port(
            "prometheus-http",
            "prometheus",
            9090,
            15090,
            "prometheus.tsw.local",
            enabled_by_default=False,
        ),
        _route_port(
            "grafana-http",
            "grafana",
            3000,
            15300,
            "grafana.tsw.local",
            enabled_by_default=False,
        ),
        _route_port(
            "tiny-swarm-frontend",
            "tiny-swarm",
            8080,
            18080,
            "app.tsw.local",
            route_name="app",
            upstream_service="tiny-swarm",
            enabled_by_default=False,
        ),
        _route_port(
            "tiny-swarm-backend",
            "tiny-swarm",
            8081,
            18081,
            "api.tsw.local",
            route_name="api",
            upstream_service="tiny-swarm",
            enabled_by_default=False,
        ),
    ]


def _port(
    port_id: str,
    service_id: str,
    internal_port: int,
    external_port: int,
) -> dict[str, Any]:
    return {
        "id": port_id,
        "service_id": service_id,
        "internal_port": internal_port,
        "external_port": external_port,
        "exposure": "diagnostic",
        "protocol": "tcp",
        "required_for_preflight": False,
    }


def _route_port(
    port_id: str,
    service_id: str,
    internal_port: int,
    external_port: int,
    route_host: str,
    *,
    route_name: str | None = None,
    upstream_service: str | None = None,
    health_path: str | None = None,
    enabled_by_default: bool = True,
) -> dict[str, Any]:
    payload = _port(port_id, service_id, internal_port, external_port)
    metadata = {
        "route_enabled_by_default": str(enabled_by_default).lower(),
        "upstream_service": upstream_service or service_id,
    }
    if route_name is not None:
        metadata["route_name"] = route_name
    if health_path is not None:
        metadata["health_path"] = health_path
        metadata["service_access_path"] = health_path
    payload["route_host"] = route_host
    payload["metadata"] = metadata
    return payload


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sink = StringIO()
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.dump(payload, sink)
    path.write_text(sink.getvalue(), encoding="utf-8")
