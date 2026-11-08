from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, cast
from urllib.parse import urlparse

from ruamel.yaml import YAML

from tiny_swarm_world.domain.ingress import desired_https_ingress_for_profile
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)

@dataclass(frozen=True)
class RouteExpectation:
    route_name: str
    stack_name: str
    service_name: str
    router_name: str
    hostname: str
    upstream_service: str
    upstream_port: int
    dashboard_url: str


ROUTE_EXPECTATIONS: dict[str, RouteExpectation] = {
    "service-access": RouteExpectation(
        route_name="service-access",
        stack_name="service-access",
        service_name="service-access-dashboard",
        router_name="service-access",
        hostname="service-access.tsw.local",
        upstream_service="service-access-dashboard",
        upstream_port=80,
        dashboard_url="https://service-access.tsw.local",
    ),
    "portainer": RouteExpectation(
        route_name="portainer",
        stack_name="portainer",
        service_name="portainer",
        router_name="portainer",
        hostname="portainer.tsw.local",
        upstream_service="portainer",
        upstream_port=9000,
        dashboard_url="https://portainer.tsw.local",
    ),
    "jenkins": RouteExpectation(
        route_name="jenkins",
        stack_name="jenkins",
        service_name="jenkins",
        router_name="jenkins",
        hostname="jenkins.tsw.local",
        upstream_service="jenkins",
        upstream_port=8080,
        dashboard_url="https://jenkins.tsw.local",
    ),
    "sonarqube": RouteExpectation(
        route_name="sonarqube",
        stack_name="sonarqube",
        service_name="sonarqube",
        router_name="sonarqube",
        hostname="sonarqube.tsw.local",
        upstream_service="sonarqube",
        upstream_port=9000,
        dashboard_url="https://sonarqube.tsw.local",
    ),
    "nexus": RouteExpectation(
        route_name="nexus",
        stack_name="nexus",
        service_name="nexus",
        router_name="nexus",
        hostname="nexus.tsw.local",
        upstream_service="nexus",
        upstream_port=8081,
        dashboard_url="https://nexus.tsw.local",
    ),
    "swagger": RouteExpectation(
        route_name="swagger",
        stack_name="swagger",
        service_name="swagger-nginx",
        router_name="swagger",
        hostname="swagger.tsw.local",
        upstream_service="swagger-nginx",
        upstream_port=8084,
        dashboard_url="https://swagger.tsw.local",
    ),
    "infisical": RouteExpectation(
        route_name="infisical",
        stack_name="infisical",
        service_name="infisical",
        router_name="infisical",
        hostname="infisical.tsw.local",
        upstream_service="infisical",
        upstream_port=8080,
        dashboard_url="https://infisical.tsw.local",
    ),
    "pulsar-manager": RouteExpectation(
        route_name="pulsar-manager",
        stack_name="pulsar",
        service_name="pulsar-manager",
        router_name="pulsar",
        hostname="pulsar.tsw.local",
        upstream_service="pulsar-manager",
        upstream_port=9527,
        dashboard_url="https://pulsar.tsw.local",
    ),
    "pulsar-admin-api": RouteExpectation(
        route_name="pulsar-admin-api",
        stack_name="pulsar",
        service_name="pulsar",
        router_name="pulsar-api",
        hostname="pulsar-api.tsw.local",
        upstream_service="pulsar",
        upstream_port=8080,
        dashboard_url="https://pulsar-api.tsw.local/admin/v2/clusters",
    ),
}


def route_expectation(route_name: str) -> RouteExpectation:
    return ROUTE_EXPECTATIONS[route_name]


def desired_route_by_name(route_name: str) -> dict[str, Any]:
    desired = desired_https_ingress_for_profile(
        port_registry=PortRegistryYamlRepository().load()
    )
    routes = {route.service_name: route.to_dict() for route in desired.routes}
    return routes[route_name]


def dashboard_links() -> tuple[str, ...]:
    parser = _LinkCollector()
    parser.feed(ComposeFileRepositoryYaml().render_service_access_dashboard())
    return tuple(dict.fromkeys(parser.links))


def compose_service(expectation: RouteExpectation) -> dict[str, Any]:
    stack_definition = ComposeFileRepositoryYaml().get_compose_of(expectation.stack_name)
    compose = cast(
        dict[str, Any],
        YAML(typ="safe").load(stack_definition.compose_content),
    )
    return cast(dict[str, Any], compose["services"][expectation.service_name])


def traefik_labels(expectation: RouteExpectation) -> set[str]:
    service = compose_service(expectation)
    deploy = service.get("deploy", {})
    return set(deploy.get("labels", ()))


def route_evidence(route_names: tuple[str, ...] = tuple(ROUTE_EXPECTATIONS)) -> dict[str, Any]:
    desired = desired_https_ingress_for_profile(
        port_registry=PortRegistryYamlRepository().load()
    ).to_dict()
    selected = set(route_names)
    routes = cast(list[dict[str, Any]], desired["routes"])
    desired["routes"] = [route for route in routes if route["service_name"] in selected]
    return desired


def assert_routed_url_shape(testcase, url: str) -> None:
    parsed = urlparse(url)
    testcase.assertEqual("https", parsed.scheme)
    testcase.assertTrue(parsed.hostname and parsed.hostname.endswith(".tsw.local"))
    testcase.assertIsNone(parsed.port)
    testcase.assertFalse(parsed.username)
    testcase.assertFalse(parsed.password)
    testcase.assertFalse(parsed.query)
    testcase.assertFalse(parsed.fragment)


def assert_route_contract(testcase, route_name: str) -> None:
    expectation = route_expectation(route_name)
    route = desired_route_by_name(route_name)
    labels = traefik_labels(expectation)
    service = compose_service(expectation)

    testcase.assertEqual(expectation.hostname, route["hostname"])
    testcase.assertEqual(expectation.upstream_service, route["upstream_service"])
    testcase.assertEqual(expectation.upstream_port, route["upstream_port"])
    testcase.assertIn("service_access_link", service["networks"])
    testcase.assertIn("traefik.enable=true", labels)
    testcase.assertIn("traefik.swarm.network=service_access_link", labels)
    rule_prefix = f"traefik.http.routers.{expectation.router_name}.rule="
    rule_labels = [label for label in labels if label.startswith(rule_prefix)]
    testcase.assertTrue(rule_labels, f"missing Traefik rule label for {expectation.router_name}")
    testcase.assertTrue(
        any(f"Host(`{expectation.hostname}`)" in label for label in rule_labels),
        f"missing preferred routed host {expectation.hostname}",
    )
    testcase.assertFalse(
        any("Host(`localhost`)" in label for label in rule_labels),
        f"unexpected localhost compatibility host in preferred route {expectation.router_name}",
    )
    testcase.assertIn(
        f"traefik.http.routers.{expectation.router_name}.entrypoints=websecure",
        labels,
    )
    testcase.assertIn(
        f"traefik.http.routers.{expectation.router_name}.tls=true",
        labels,
    )
    testcase.assertIn(
        "traefik.http.services."
        f"{expectation.router_name}.loadbalancer.server.port={expectation.upstream_port}",
        labels,
    )


def assert_dashboard_prefers_route(testcase, route_name: str) -> None:
    expectation = route_expectation(route_name)
    links = dashboard_links()

    testcase.assertIn(expectation.dashboard_url, links)
    assert_routed_url_shape(testcase, expectation.dashboard_url)
    for link in links:
        parsed = urlparse(link)
        testcase.assertNotIn(parsed.port, {10080, 10443})


def assert_evidence_safe(testcase, evidence: object) -> None:
    text = repr(evidence).casefold()
    for fragment in (
        "password",
        "secret",
        "token",
        "-----begin",
        "private key",
        "127.0.0.1",
    ):
        testcase.assertNotIn(fragment, text)


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = {key: value or "" for key, value in attrs}
        href = attributes.get("href")
        if href:
            self.links.append(href)
