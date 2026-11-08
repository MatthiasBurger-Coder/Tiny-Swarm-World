"""Ordered service-probe strategies for host preflight matching."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol


class HttpAvailability(Protocol):
    def __call__(
        self,
        port: int,
        paths: Sequence[str],
        expected_markers: Sequence[str],
        *,
        scheme: str = "http",
    ) -> bool:
        pass


class ServiceProbe(Protocol):
    def supports(self, service: str) -> bool:
        pass

    def matches(self, port: int) -> bool:
        pass


@dataclass(frozen=True, slots=True)
class HttpServiceProbe:
    service_pattern: str
    http_probe: HttpAvailability
    paths: tuple[str, ...]
    expected_markers: tuple[str, ...]
    scheme: str = "http"

    def supports(self, service: str) -> bool:
        return self.service_pattern in service.casefold()

    def matches(self, port: int) -> bool:
        return self.http_probe(
            port,
            self.paths,
            self.expected_markers,
            scheme=self.scheme,
        )


@dataclass(frozen=True, slots=True)
class CallbackServiceProbe:
    service_pattern: str
    matcher: Callable[[int], bool]

    def supports(self, service: str) -> bool:
        return self.service_pattern in service.casefold()

    def matches(self, port: int) -> bool:
        return self.matcher(port)


@dataclass(frozen=True, slots=True)
class ServiceProbeRegistry:
    probes: tuple[ServiceProbe, ...]

    def matches(self, port: int, service: str) -> bool:
        for probe in self.probes:
            if probe.supports(service):
                return probe.matches(port)
        return False


def default_service_probe_registry(
    *,
    http_probe: HttpAvailability,
    service_access_probe: Callable[[int], bool],
    tcp_probe: Callable[[int], bool],
    api_status_path: str,
    service_access_text: str,
) -> ServiceProbeRegistry:
    """Create the compatibility-ordered service registry."""

    return ServiceProbeRegistry(
        probes=(
            HttpServiceProbe(
                "portainer",
                http_probe,
                (api_status_path, "/api/system/status"),
                ("version",),
            ),
            HttpServiceProbe("docker registry", http_probe, ("/v2/",), ()),
            HttpServiceProbe(
                "nexus",
                http_probe,
                ("/service/rest/v1/status", "/"),
                ("nexus", "status", "available"),
            ),
            HttpServiceProbe("jenkins", http_probe, ("/login", "/"), ("jenkins",)),
            HttpServiceProbe(
                "pulsar admin",
                http_probe,
                ("/admin/v2/clusters",),
                ("standalone", "clusters"),
            ),
            HttpServiceProbe(
                "pulsar manager",
                http_probe,
                ("/",),
                ("pulsar", "manager"),
            ),
            CallbackServiceProbe("pulsar broker", tcp_probe),
            HttpServiceProbe(
                "sonarqube",
                http_probe,
                ("/api/system/status", "/"),
                ("sonar", "status"),
            ),
            HttpServiceProbe(
                "swagger api",
                http_probe,
                ("/",),
                ("access-control-allow-origin: *",),
            ),
            HttpServiceProbe("swagger", http_probe, ("/",), ("swagger", "openapi")),
            HttpServiceProbe("traefik http ingress", http_probe, ("/",), ("traefik",)),
            HttpServiceProbe(
                "traefik https ingress",
                http_probe,
                ("/",),
                ("traefik",),
                scheme="https",
            ),
            CallbackServiceProbe(service_access_text, service_access_probe),
            HttpServiceProbe(
                "infisical https",
                http_probe,
                ("/", api_status_path),
                ("infisical", "content-security-policy"),
                scheme="https",
            ),
            HttpServiceProbe(
                "infisical",
                http_probe,
                ("/", api_status_path),
                ("infisical",),
            ),
        )
    )
