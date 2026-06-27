import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from ruamel.yaml import YAML

from tiny_swarm_world.domain.ingress import desired_https_ingress_for_profile


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_PATH = (
    REPOSITORY_ROOT
    / "infra"
    / "config"
    / "compose"
    / "service-access"
    / "dashboard"
    / "index.html"
)


class TestServiceAccessRouting(unittest.TestCase):
    def test_service_access_links_prefer_traefik_routed_urls(self):
        links = _dashboard_links()

        self.assertLessEqual(
            {
                "https://service-access.tsw.local",
                "https://portainer.tsw.local",
                "https://jenkins.tsw.local",
                "https://sonarqube.tsw.local",
                "https://nexus.tsw.local",
                "https://pulsar-api.tsw.local/admin/v2/clusters",
                "https://pulsar.tsw.local",
                "https://swagger.tsw.local",
                "https://infisical.tsw.local",
            },
            set(links),
        )
        for link in links:
            parsed = urlparse(link)
            self.assertEqual("https", parsed.scheme)
            self.assertTrue(parsed.hostname and parsed.hostname.endswith(".tsw.local"))
            self.assertIsNone(parsed.port)
            self.assertFalse(parsed.username)
            self.assertFalse(parsed.password)
            self.assertFalse(parsed.query)

    def test_effective_route_evidence_is_redacted_and_lists_fallbacks(self):
        desired = desired_https_ingress_for_profile()
        evidence = {
            "gateway_public_ingress_ports": list(desired.public_ports),
            "diagnostic_fallback_ports": [
                {"port": 10080, "classification": "diagnostic"},
                {"port": 10443, "classification": "diagnostic"},
            ],
            "routes": [route.to_dict() for route in desired.routes],
            "service_access_preferred_url_source": "traefik_host_route",
            "skipped_routes": [
                {"service": "rabbitmq", "reason": "service_not_supported"},
            ],
        }

        self.assertEqual([80, 443], evidence["gateway_public_ingress_ports"])
        self.assertTrue(_evidence_safe(evidence))
        self.assertNotIn("rabbitmq.tsw.local", repr(evidence))
        self.assertIn("service-access.tsw.local", repr(evidence))

    def test_service_access_and_optional_routes_have_traefik_labels(self):
        expected = {
            "service-access": (
                "service-access-dashboard",
                "service-access",
                "service-access.tsw.local",
                "80",
            ),
            "pulsar": ("pulsar-manager", "pulsar", "pulsar.tsw.local", "9527"),
            "pulsar-api": ("pulsar", "pulsar-api", "pulsar-api.tsw.local", "8080"),
            "swagger": ("swagger-nginx", "swagger", "swagger.tsw.local", "8084"),
        }

        for stack_name, (service_name, router_name, hostname, port) in expected.items():
            compose = _compose_data(_stack_for_route(stack_name))
            service = compose["services"][service_name]
            labels = set(service["deploy"]["labels"])
            with self.subTest(stack_name=stack_name):
                self.assertIn("traefik_ingress", service["networks"])
                self.assertIn(f"traefik.http.routers.{router_name}.rule=Host(`{hostname}`)", labels)
                self.assertIn(f"traefik.http.routers.{router_name}.entrypoints=websecure", labels)
                self.assertIn(f"traefik.http.routers.{router_name}.tls=true", labels)
                self.assertIn(
                    f"traefik.http.services.{router_name}.loadbalancer.server.port={port}",
                    labels,
                )


def _stack_for_route(route_name: str) -> str:
    if route_name in {"pulsar", "pulsar-api"}:
        return "pulsar"
    return route_name


def _dashboard_links() -> list[str]:
    parser = _LinkCollector()
    parser.feed(DASHBOARD_PATH.read_text(encoding="utf-8"))
    return parser.links


def _compose_data(stack_name: str) -> dict[str, object]:
    compose_path = REPOSITORY_ROOT / "infra" / "config" / "compose" / stack_name / "docker-compose.yml"
    return YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))


def _evidence_safe(value: object) -> bool:
    text = repr(value).casefold()
    return not any(
        fragment in text
        for fragment in ("password", "secret", "token", "-----begin", "private key", "127.0.0.1")
    )


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = {key: value or "" for key, value in attrs}
        href = attributes.get("href")
        if href:
            self.links.append(href)


if __name__ == "__main__":
    unittest.main()
