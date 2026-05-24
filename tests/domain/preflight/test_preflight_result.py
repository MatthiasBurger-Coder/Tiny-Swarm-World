import unittest

from tiny_swarm_world.domain.preflight import (
    LIVE_CONSENT_ENVIRONMENT_VALUE,
    LIVE_CONSENT_PHRASE,
    LiveConsent,
    PreflightCategory,
    PreflightCheck,
    PreflightResult,
    PreflightSeverity,
    PreflightStatus,
    SetupManifest,
    SetupPortRequirement,
    SetupProfile,
    SetupSecretRequirement,
    SetupServiceRequirement,
    default_preflight_configuration,
    default_setup_manifest,
)


class TestLiveConsent(unittest.TestCase):
    def test_accepts_short_live_confirmation(self):
        consent = LiveConsent(live_flag=True, confirmed=True)

        self.assertTrue(consent.accepted)
        self.assertEqual((), consent.missing_reasons)

    def test_accepts_legacy_exact_live_consent_contract(self):
        consent = LiveConsent(
            live_flag=True,
            environment_value=LIVE_CONSENT_ENVIRONMENT_VALUE,
            typed_phrase=LIVE_CONSENT_PHRASE,
        )

        self.assertTrue(consent.accepted)
        self.assertEqual((), consent.missing_reasons)

    def test_reports_missing_live_consent_controls_without_values(self):
        consent = LiveConsent(live_flag=False)

        self.assertFalse(consent.accepted)
        self.assertEqual(("missing --live",), consent.missing_reasons)

    def test_reports_missing_short_confirmation(self):
        consent = LiveConsent(live_flag=True, confirmed=False)

        self.assertFalse(consent.accepted)
        self.assertEqual(("missing live confirmation",), consent.missing_reasons)


class TestPreflightResult(unittest.TestCase):
    def test_result_fails_when_any_check_fails(self):
        passing = PreflightCheck(
            check_id="HOST",
            category=PreflightCategory.HOST,
            status=PreflightStatus.PASSED,
            severity=PreflightSeverity.MANDATORY,
            message="Host is ready.",
            remediation="None",
        )
        failing = PreflightCheck(
            check_id="SECRET",
            category=PreflightCategory.SECRET,
            status=PreflightStatus.FAILED,
            severity=PreflightSeverity.MANDATORY,
            message="Secret is missing.",
            remediation="Provide the secret source.",
        )

        result = PreflightResult((passing, failing))

        self.assertFalse(result.passed)
        self.assertEqual((failing,), result.failed_checks)
        self.assertEqual("FAILED", result.to_dict()["status"])
        self.assertEqual("full", result.to_dict()["setup_profile"])

    def test_check_evidence_is_immutable_and_serializable(self):
        evidence = {"path": ".env"}
        check = PreflightCheck(
            check_id="IGNORE",
            category=PreflightCategory.IGNORE_POLICY,
            status=PreflightStatus.PASSED,
            severity=PreflightSeverity.MANDATORY,
            message="Path ignored.",
            remediation="None",
            evidence=evidence,
        )
        evidence["path"] = "changed"

        self.assertEqual(".env", check.evidence["path"])
        self.assertEqual(".env", check.to_dict()["evidence"]["path"])

    def test_default_forbidden_secret_fingerprints_do_not_expose_raw_values(self):
        configuration_text = repr(default_preflight_configuration())
        raw_values = (
            "admin" + "1234567890",
            "MyAdmin" + "PassWord1234",
            "PORTAINER" + "_TOKEN",
        )

        for raw_value in raw_values:
            self.assertNotIn(raw_value, configuration_text)

    def test_resource_only_failures_are_not_reported_as_full_pass(self):
        resource_failure = PreflightCheck(
            check_id="RESOURCE-CPU",
            category=PreflightCategory.RESOURCE,
            status=PreflightStatus.FAILED,
            severity=PreflightSeverity.RESOURCE_GATED,
            message="CPU resource threshold is not satisfied.",
            remediation="Provide more CPU capacity.",
        )

        result = PreflightResult((resource_failure,))

        self.assertFalse(result.passed)
        self.assertTrue(result.resource_gated)
        self.assertEqual("RESOURCE_GATED", result.status)
        self.assertEqual("RESOURCE_GATED", result.to_dict()["status"])

    def test_default_setup_manifest_is_structured_and_secret_safe(self):
        manifest = default_setup_manifest()
        first_secret = manifest.to_dict()["services"][0]["secrets"][0]

        self.assertEqual(SetupProfile.FULL, manifest.profile)
        self.assertIn("Portainer", manifest.service_names)
        self.assertIn("TSW_PORTAINER_PASSWORD", first_secret["name"])
        self.assertNotIn("password_value", repr(manifest.to_dict()).lower())
        self.assertTrue(manifest.evidence_root.startswith(".tiny-swarm-world/"))

    def test_default_setup_manifest_lists_every_full_service_contract(self):
        manifest = default_setup_manifest()

        self.assertEqual(
            (
                "Portainer",
                "Nexus",
                "Jenkins",
                "RabbitMQ",
                "SonarQube",
                "Swagger/NGINX",
            ),
            manifest.service_names,
        )
        self.assertEqual(
            (9000, 8081, 5000, 8080, 5672, 15672, 9001, 80),
            tuple(port.port for port in manifest.required_ports),
        )
        self.assertEqual(
            (
                "TSW_PORTAINER_PASSWORD",
                "TSW_NEXUS_ADMIN_PASSWORD",
                "TSW_JENKINS_ADMIN_PASSWORD",
                "TSW_RABBITMQ_PASSWORD",
                "TSW_SONARQUBE_ADMIN_PASSWORD",
                "TSW_POSTGRES_PASSWORD",
            ),
            tuple(secret.name for secret in manifest.required_secrets),
        )

    def test_resource_gated_manifest_keeps_profile_explicit(self):
        manifest = default_setup_manifest(SetupProfile.RESOURCE_GATED)

        self.assertEqual(SetupProfile.RESOURCE_GATED, manifest.profile)
        self.assertEqual("resource-gated", manifest.summary()["profile"])
        self.assertEqual(tuple(manifest.summary()["services"]), manifest.service_names)

    def test_setup_manifest_rejects_non_local_evidence_paths(self):
        with self.assertRaises(ValueError):
            SetupManifest(
                profile=SetupProfile.FULL,
                services=(SetupServiceRequirement("Portainer"),),
                evidence_root="/tmp/evidence",
            )

    def test_setup_manifest_rejects_path_traversal_evidence_paths(self):
        with self.assertRaises(ValueError):
            SetupManifest(
                profile=SetupProfile.FULL,
                services=(
                    SetupServiceRequirement(
                        "Portainer",
                        ports=(SetupPortRequirement(9000, "Portainer"),),
                        secrets=(SetupSecretRequirement("TSW_PORTAINER_PASSWORD", "Portainer"),),
                    ),
                ),
                evidence_root=".tiny-swarm-world/../leak",
            )
