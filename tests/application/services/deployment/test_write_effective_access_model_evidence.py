from __future__ import annotations

import json
import os
import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from tests.support.sonar_safe_literals import sample_text
from tiny_swarm_world.application.ports.repositories.port_effective_access_model_repository import (
    PortEffectiveAccessModelRepository,
)
from tiny_swarm_world.application.ports.repositories.port_routing_evidence_repository import (
    EffectiveAccessModelEvidence,
    PortRoutingEvidenceRepository,
)
from tiny_swarm_world.application.services.deployment.write_effective_access_model_evidence import (
    WriteEffectiveAccessModelEvidence,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.ingress import (
    CredentialReference,
    DiagnosticFallbackPort,
    DesiredHttpsIngress,
    DesiredHttpsRoute,
    SkippedRoute,
)


FIXED_TIME = datetime(2026, 7, 11, 12, 30, 45, tzinfo=UTC)


class _EffectiveAccessModelRepository(PortEffectiveAccessModelRepository):
    def __init__(self, model: DesiredHttpsIngress):
        self.model = model
        self.calls = 0

    def get_effective_access_model(self) -> DesiredHttpsIngress:
        self.calls += 1
        return self.model


class _RoutingEvidenceRepository(PortRoutingEvidenceRepository):
    def __init__(self):
        self.evidence: EffectiveAccessModelEvidence | None = None

    def write_effective_access_model(self, evidence: EffectiveAccessModelEvidence) -> None:
        self.evidence = evidence


class TestWriteEffectiveAccessModelEvidence(unittest.TestCase):
    def test_writes_complete_redacted_allowlisted_evidence(self):
        secret_note = sample_text("operator", "-only", "-value")
        private_key_marker = sample_text("private", "-key", "-value")
        environment_secret = sample_text("environment", "-credential", "-value")
        model_repository = _EffectiveAccessModelRepository(
            _access_model(secret_note=secret_note, no_login_note=private_key_marker)
        )
        evidence_repository = _RoutingEvidenceRepository()
        use_case = WriteEffectiveAccessModelEvidence(
            model_repository,
            evidence_repository,
            ServiceStackProfile.SERVICE_ACCESS,
            clock=lambda: FIXED_TIME,
        )

        with patch.dict(os.environ, {"TSW_TEST_CREDENTIAL": environment_secret}):
            evidence = use_case.run()

        self.assertIs(evidence_repository.evidence, evidence)
        self.assertEqual(1, model_repository.calls)
        payload = evidence.to_dict()
        self.assertEqual(
            {
                "diagnostic_fallback_ports",
                "evidence_kind",
                "gateway_public_ingress_ports",
                "generated_at",
                "health_check_targets",
                "public_ports",
                "result",
                "routes",
                "service_access_links",
                "service_access_preferred_url_source",
                "service_profile",
                "skipped_routes",
            },
            set(payload),
        )
        self.assertEqual("effective_access_model", payload["evidence_kind"])
        self.assertEqual("2026-07-11T12:30:45Z", payload["generated_at"])
        self.assertEqual("service-access", payload["service_profile"])
        self.assertEqual([80, 443], payload["public_ports"])
        self.assertEqual([80, 443], payload["gateway_public_ingress_ports"])
        self.assertEqual("traefik_host_route", payload["service_access_preferred_url_source"])
        self.assertEqual("generated", payload["result"])
        routes = payload["routes"]
        self.assertIsInstance(routes, list)
        assert isinstance(routes, list)
        credential = routes[1]["credential"]
        self.assertEqual(
            {"item_reference": "platform/zulu", "username_label": "ops-admin"},
            credential,
        )
        serialized = json.dumps(payload, sort_keys=True)
        self.assertNotIn(secret_note, serialized)
        self.assertNotIn(private_key_marker, serialized)
        self.assertNotIn(environment_secret, serialized)
        self.assertNotIn("note", credential)
        self.assertEqual(
            {"item_reference": "platform/zulu", "username_label": "ops-admin"},
            payload["service_access_links"][1]["credential"],
        )
        self.assertEqual(
            ["alpha", "zulu"],
            [target["service"] for target in payload["health_check_targets"]],
        )
        self.assertEqual(
            ["alpha", "zulu"],
            [link["service"] for link in payload["service_access_links"]],
        )

    def test_sorts_every_repeated_evidence_collection_deterministically(self):
        forward_repository = _RoutingEvidenceRepository()
        reverse_repository = _RoutingEvidenceRepository()
        WriteEffectiveAccessModelEvidence(
            _EffectiveAccessModelRepository(_access_model()),
            forward_repository,
            ServiceStackProfile.SERVICE_ACCESS,
            clock=lambda: FIXED_TIME,
        ).run()
        WriteEffectiveAccessModelEvidence(
            _EffectiveAccessModelRepository(_access_model(reverse=True)),
            reverse_repository,
            ServiceStackProfile.SERVICE_ACCESS,
            clock=lambda: FIXED_TIME,
        ).run()

        self.assertIsNotNone(forward_repository.evidence)
        self.assertIsNotNone(reverse_repository.evidence)
        assert forward_repository.evidence is not None
        assert reverse_repository.evidence is not None
        self.assertEqual(
            forward_repository.evidence.to_dict(),
            reverse_repository.evidence.to_dict(),
        )
        payload = forward_repository.evidence.to_dict()
        self.assertEqual(
            ["alpha", "zulu"],
            [route["service_name"] for route in payload["routes"]],
        )
        self.assertEqual(
            ["alpha", "zulu"],
            [route["service"] for route in payload["skipped_routes"]],
        )
        self.assertEqual(
            ["alpha", "zulu"],
            [port["service"] for port in payload["diagnostic_fallback_ports"]],
        )

    def test_rejects_credential_bearing_url_without_writing_evidence(self):
        unsafe_model = DesiredHttpsIngress(
            routes=(
                DesiredHttpsRoute(
                    service_name="alpha",
                    hostname="alpha.tsw.local",
                    upstream_service="alpha",
                    upstream_port=8080,
                    service_access_url="https://operator:value@alpha.tsw.local",
                ),
            )
        )
        evidence_repository = _RoutingEvidenceRepository()
        use_case = WriteEffectiveAccessModelEvidence(
            _EffectiveAccessModelRepository(unsafe_model),
            evidence_repository,
            ServiceStackProfile.SERVICE_ACCESS,
            clock=lambda: FIXED_TIME,
        )

        with self.assertRaisesRegex(ValueError, "safe routed HTTPS URL"):
            use_case.run()

        self.assertIsNone(evidence_repository.evidence)


def _access_model(
    *,
    reverse: bool = False,
    secret_note: str = "Open in secret store",
    no_login_note: str = "No login required",
) -> DesiredHttpsIngress:
    routes: tuple[DesiredHttpsRoute, ...] = (
        DesiredHttpsRoute(
            service_name="zulu",
            hostname="zulu.tsw.local",
            upstream_service="zulu-api",
            upstream_port=9090,
            health_check_url="https://zulu.tsw.local/health",
            service_access_url="https://zulu.tsw.local/ui",
            credential=CredentialReference(
                username_label="ops-admin",
                item_reference="platform/zulu",
                note=secret_note,
            ),
        ),
        DesiredHttpsRoute(
            service_name="alpha",
            hostname="alpha.tsw.local",
            upstream_service="alpha-api",
            upstream_port=8080,
            no_login_note=no_login_note,
        ),
    )
    fallback_ports: tuple[DiagnosticFallbackPort, ...] = (
        DiagnosticFallbackPort("zulu-http", "zulu", 19090, "diagnostic"),
        DiagnosticFallbackPort("alpha-http", "alpha", 18080, "compatibility"),
    )
    skipped_routes: tuple[SkippedRoute, ...] = (
        SkippedRoute("zulu", "service_not_enabled"),
        SkippedRoute("alpha", "service_not_enabled"),
    )
    if reverse:
        routes = tuple(reversed(routes))
        fallback_ports = tuple(reversed(fallback_ports))
        skipped_routes = tuple(reversed(skipped_routes))
    return DesiredHttpsIngress(
        routes=routes,
        diagnostic_fallback_ports=fallback_ports,
        skipped_routes=skipped_routes,
    )
