from datetime import UTC, datetime
import unittest

from tests.support.sonar_safe_literals import sensitive_assignment

from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.ingress import (
    CertificateSummary,
    desired_https_ingress_for_profile,
)
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


class TestCertificateSummary(unittest.TestCase):
    def test_valid_certificate_summary_covers_desired_ingress(self):
        desired = _desired_service_access_ingress()
        certificate = _certificate_summary(san_dns_names=desired.hostnames)

        result = certificate.validation_for(
            desired,
            checked_at_utc=datetime(2026, 6, 9, tzinfo=UTC),
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.problems, ())
        self.assertEqual(
            certificate.to_dict(),
            {
                "chain_verified": True,
                "common_name": "tsw.local ingress",
                "extended_key_usage": ["server_auth"],
                "issuer": "operator existing ca",
                "key_usage": ["digital_signature", "key_encipherment"],
                "not_after_utc": "2027-06-09T00:00:00+00:00",
                "not_before_utc": "2026-06-01T00:00:00+00:00",
                "san_dns_names": list(desired.hostnames),
            },
        )

    def test_certificate_validation_reports_missing_policy_requirements(self):
        desired = _desired_service_access_ingress()
        certificate = _certificate_summary(
            san_dns_names=("jenkins.tsw.local",),
            not_after_utc=datetime(2026, 6, 8, tzinfo=UTC),
            key_usage=("digital_signature",),
            extended_key_usage=("client_auth",),
            chain_verified=False,
        )

        result = certificate.validation_for(
            desired,
            checked_at_utc=datetime(2026, 6, 9, tzinfo=UTC),
        )

        self.assertFalse(result.passed)
        self.assertEqual(
            result.missing_san_dns_names,
            (
                "portainer.tsw.local",
                "nexus.tsw.local",
                "pulsar-api.tsw.local",
                "pulsar.tsw.local",
                "sonarqube.tsw.local",
                "swagger.tsw.local",
                "infisical.tsw.local",
                "service-access.tsw.local",
            ),
        )
        self.assertEqual(
            result.problems,
            (
                "missing_san_dns_names",
                "expired",
                "key_usage_incomplete",
                "extended_key_usage_incomplete",
                "chain_not_verified",
            ),
        )

    def test_certificate_summary_rejects_raw_secret_or_path_material(self):
        unsafe_values = (
            "-----BEGIN PRIVATE KEY-----",
            "certificate at /home/operator/ingress.crt",
            f"issuer {sensitive_assignment()}",
            "issuer at 192.168.1.10",
        )

        for unsafe_value in unsafe_values:
            with self.subTest(unsafe_value=unsafe_value):
                with self.assertRaises(ValueError):
                    _certificate_summary(issuer=unsafe_value)

    def test_certificate_summary_requires_utc_validity_window(self):
        with self.assertRaises(ValueError):
            _certificate_summary(
                not_before_utc=datetime(2026, 6, 1),
                not_after_utc=datetime(2027, 6, 9, tzinfo=UTC),
            )

        with self.assertRaises(ValueError):
            _certificate_summary(
                not_before_utc=datetime(2027, 6, 9, tzinfo=UTC),
                not_after_utc=datetime(2026, 6, 1, tzinfo=UTC),
            )


def _certificate_summary(
    *,
    common_name: str = "tsw.local ingress",
    san_dns_names: tuple[str, ...] = ("jenkins.tsw.local",),
    issuer: str = "operator existing ca",
    not_before_utc: datetime = datetime(2026, 6, 1, tzinfo=UTC),
    not_after_utc: datetime = datetime(2027, 6, 9, tzinfo=UTC),
    key_usage: tuple[str, ...] = ("digital_signature", "key_encipherment"),
    extended_key_usage: tuple[str, ...] = ("server_auth",),
    chain_verified: bool = True,
) -> CertificateSummary:
    return CertificateSummary(
        common_name=common_name,
        san_dns_names=san_dns_names,
        issuer=issuer,
        not_before_utc=not_before_utc,
        not_after_utc=not_after_utc,
        key_usage=key_usage,
        extended_key_usage=extended_key_usage,
        chain_verified=chain_verified,
    )


def _desired_service_access_ingress():
    return desired_https_ingress_for_profile(
        ServiceStackProfile.SERVICE_ACCESS,
        port_registry=PortRegistryYamlRepository().load(),
    )


if __name__ == "__main__":
    unittest.main()
