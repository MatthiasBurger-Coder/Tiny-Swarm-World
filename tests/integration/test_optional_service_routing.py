from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch
from urllib.parse import urlparse

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_effective_access_model_repository import (
    PortEffectiveAccessModelRepository,
)
from tiny_swarm_world.domain.ingress import DesiredHttpsIngress, DesiredHttpsRoute
from tests.support.effective_access_model_fixture import (
    CORE_ROUTE_EXPECTATIONS,
    OPTIONAL_ROUTE_EXPECTATIONS,
    EffectiveAccessModelFixture,
    effective_access_model_fixture,
)


class TestOptionalServiceRouting(unittest.TestCase):
    def test_prometheus_route_is_generated_when_prometheus_is_enabled(self) -> None:
        self._assert_optional_route("prometheus", "prometheus")

    def test_grafana_route_is_generated_when_grafana_is_enabled(self) -> None:
        self._assert_optional_route("grafana", "grafana")

    def test_app_route_is_generated_when_app_is_enabled(self) -> None:
        self._assert_optional_route("app", "app")

    def test_api_route_is_generated_when_api_is_enabled(self) -> None:
        self._assert_optional_route("api", "api")

    def test_app_and_api_labels_coexist_on_the_shared_upstream_service(self) -> None:
        with effective_access_model_fixture(
            enabled_services=("tiny-swarm",)
        ) as fixture:
            model = fixture.repository.get_effective_access_model()
            optional_routes = {
                route.service_name: route
                for route in model.routes
                if route.service_name in {"app", "api"}
            }
            compose = _rendered_compose(fixture, "tiny-swarm")
            service = cast(dict[str, Any], compose["services"]["tiny-swarm"])
            labels = cast(list[str], service["deploy"]["labels"])
            service_access_links = cast(
                list[dict[str, object]],
                model.to_dict()["service_access_links"],
            )

        self.assertEqual(set(optional_routes), {"app", "api"})
        self.assertEqual(labels.count("traefik.enable=true"), 1)
        self.assertEqual(
            labels.count("traefik.swarm.network=service_access_link"),
            1,
        )
        for route_name, upstream_port in (("app", 8080), ("api", 8081)):
            with self.subTest(route_name=route_name):
                self.assertIn(
                    f"traefik.http.routers.{route_name}.service={route_name}",
                    labels,
                )
                self.assertIn(
                    "traefik.http.services."
                    f"{route_name}.loadbalancer.server.port={upstream_port}",
                    labels,
                )
        self.assertEqual(service["networks"].count("service_access_link"), 1)
        self.assertEqual(
            {
                cast(str, link["url"])
                for link in service_access_links
                if link["service"] in {"app", "api"}
            },
            {"https://app.tsw.local", "https://api.tsw.local"},
        )
        self.assertFalse(
            {skipped.service_name for skipped in model.skipped_routes} & {"app", "api"}
        )

    def test_disabled_optional_routes_are_documented_as_not_enabled(self) -> None:
        with effective_access_model_fixture() as fixture:
            model = fixture.repository.get_effective_access_model()

        route_names = {route.service_name for route in model.routes}
        skips = {
            (skipped.service_name, skipped.reason) for skipped in model.skipped_routes
        }
        self.assertFalse(route_names & set(OPTIONAL_ROUTE_EXPECTATIONS))
        self.assertLessEqual(
            {
                (route_name, "service_not_enabled")
                for route_name in OPTIONAL_ROUTE_EXPECTATIONS
            },
            skips,
        )

    def test_public_effective_model_port_feeds_compose_and_dashboard(self) -> None:
        with effective_access_model_fixture(
            enabled_services=("prometheus",)
        ) as fixture:
            repository = fixture.repository
            self.assertIsInstance(repository, PortEffectiveAccessModelRepository)
            with patch.object(
                repository,
                "get_effective_access_model",
                wraps=repository.get_effective_access_model,
            ) as model_reader:
                dashboard = repository.render_service_access_dashboard()
            model_reader.assert_called_once_with()
            self.assertIn("https://prometheus.tsw.local", dashboard)

            with patch.object(
                repository,
                "get_effective_access_model",
                wraps=repository.get_effective_access_model,
            ) as model_reader:
                compose = _rendered_compose(fixture, "prometheus")
            model_reader.assert_called_once_with()

        labels = compose["services"]["prometheus"]["deploy"]["labels"]
        self.assertIn(
            "traefik.http.routers.prometheus.rule=Host(`prometheus.tsw.local`)",
            labels,
        )

    def test_core_route_model_remains_unchanged_with_isolated_configuration(
        self,
    ) -> None:
        with effective_access_model_fixture() as fixture:
            model = fixture.repository.get_effective_access_model()

        routes = {route.service_name: route for route in model.routes}
        self.assertEqual(set(CORE_ROUTE_EXPECTATIONS), set(routes))
        self.assertEqual(model.public_ports, (80, 443))
        for route_name, expectation in CORE_ROUTE_EXPECTATIONS.items():
            hostname, upstream_service, upstream_port = expectation
            route = routes[route_name]
            with self.subTest(route_name=route_name):
                self.assertEqual(hostname, route.hostname)
                self.assertEqual(upstream_service, route.upstream_service)
                self.assertEqual(upstream_port, route.upstream_port)

    def test_temporary_fixtures_do_not_change_committed_configuration(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        committed_services = repository_root / "infra" / "config" / "services.yml"
        committed_ports = repository_root / "infra" / "config" / "ports.yaml"
        services_before = committed_services.read_bytes()
        ports_before = committed_ports.read_bytes()

        with effective_access_model_fixture(
            enabled_services=("prometheus", "grafana", "tiny-swarm")
        ) as fixture:
            self.assertNotEqual(
                committed_services.resolve(),
                (fixture.project_paths.config_root / "services.yml").resolve(),
            )
            fixture.repository.get_compose_of("tiny-swarm")

        self.assertEqual(services_before, committed_services.read_bytes())
        self.assertEqual(ports_before, committed_ports.read_bytes())

    def _assert_optional_route(
        self,
        route_name: str,
        enabled_service: str,
    ) -> None:
        stack_name, hostname, upstream_service, upstream_port = (
            OPTIONAL_ROUTE_EXPECTATIONS[route_name]
        )
        with effective_access_model_fixture(
            enabled_services=(enabled_service,)
        ) as fixture:
            model = fixture.repository.get_effective_access_model()
            route = _route(model, route_name)
            compose = _rendered_compose(fixture, stack_name)
            service = cast(dict[str, Any], compose["services"][upstream_service])
            labels = cast(list[str], service["deploy"]["labels"])
            model_payload = model.to_dict()
            service_access_links = cast(
                list[dict[str, object]],
                model_payload["service_access_links"],
            )
            health_check_targets = cast(
                list[dict[str, object]],
                model_payload["health_check_targets"],
            )

        self.assertEqual(hostname, route.hostname)
        self.assertEqual(upstream_service, route.upstream_service)
        self.assertEqual(upstream_port, route.upstream_port)
        self.assertIn("service_access_link", service["networks"])
        self.assertEqual(
            compose["networks"]["service_access_link"],
            {"name": "service_access_link", "external": True},
        )
        expected_labels = {
            "traefik.enable=true",
            "traefik.swarm.network=service_access_link",
            f"traefik.http.routers.{route_name}.rule=Host(`{hostname}`)",
            f"traefik.http.routers.{route_name}.entrypoints=websecure",
            f"traefik.http.routers.{route_name}.tls=true",
            f"traefik.http.routers.{route_name}.service={route_name}",
            (
                f"traefik.http.services.{route_name}"
                f".loadbalancer.server.port={upstream_port}"
            ),
        }
        self.assertLessEqual(expected_labels, set(labels))
        link = next(
            link
            for link in service_access_links
            if link["service"] == route_name
        )
        self.assertIs(link["preferred"], True)
        self.assertEqual(link["url"], f"https://{hostname}")
        self.assertIsNone(urlparse(cast(str, link["url"])).port)
        health_target = next(
            target
            for target in health_check_targets
            if target["service"] == route_name
        )
        self.assertEqual(health_target["target"], f"https://{hostname}")
        self.assertEqual(upstream_service, health_target["upstream_service"])
        self.assertEqual(upstream_port, health_target["upstream_port"])
        self.assertNotIn(
            route_name,
            {skipped.service_name for skipped in model.skipped_routes},
        )


def _route(model: DesiredHttpsIngress, route_name: str) -> DesiredHttpsRoute:
    return next(route for route in model.routes if route.service_name == route_name)


def _rendered_compose(
    fixture: EffectiveAccessModelFixture,
    stack_name: str,
) -> dict[str, Any]:
    content = fixture.repository.get_compose_of(stack_name).compose_content
    return cast(dict[str, Any], YAML(typ="safe").load(content))


if __name__ == "__main__":
    unittest.main()
