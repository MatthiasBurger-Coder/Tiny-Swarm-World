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
    default_preflight_configuration,
)


class TestLiveConsent(unittest.TestCase):
    def test_accepts_exact_live_consent_contract(self):
        consent = LiveConsent(
            live_flag=True,
            environment_value=LIVE_CONSENT_ENVIRONMENT_VALUE,
            typed_phrase=LIVE_CONSENT_PHRASE,
        )

        self.assertTrue(consent.accepted)
        self.assertEqual((), consent.missing_reasons)

    def test_reports_missing_live_consent_controls_without_values(self):
        consent = LiveConsent(
            live_flag=False,
            environment_value=None,
            typed_phrase=None,
        )

        self.assertFalse(consent.accepted)
        self.assertIn("missing --live", consent.missing_reasons)
        self.assertIn("missing TSW_LIVE_INFRASTRUCTURE_CONSENT", consent.missing_reasons)
        self.assertIn("missing typed live confirmation phrase", consent.missing_reasons)


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
