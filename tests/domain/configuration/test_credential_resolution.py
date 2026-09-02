import json
import unittest

from tiny_swarm_world.domain.configuration.credential_resolution import (
    CredentialResolutionError,
    CredentialResolutionPhase,
    CredentialResolver,
    CredentialSource,
    SecureCredentialSource,
)
from tiny_swarm_world.domain.configuration.internal_test_credentials import INTERNAL_TEST_PASSWORD
from tiny_swarm_world.application.services.credential_resolution import (
    CREDENTIAL_SOURCE_MAP_ENVIRONMENT,
    CredentialResolutionService,
    decode_source_metadata,
)


class TestCredentialResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = CredentialResolver()

    def test_catalog_default_is_used_when_no_override_exists(self):
        resolved = self.resolver.resolve("TSW_PORTAINER_ADMIN_PASSWORD")

        self.assertEqual(CredentialSource.DEFAULT, resolved.source)
        self.assertEqual(INTERNAL_TEST_PASSWORD, resolved.value)
        self.assertEqual(
            {"key": "TSW_PORTAINER_ADMIN_PASSWORD", "source": "default"},
            resolved.evidence(),
        )

    def test_operator_value_overrides_catalog_default(self):
        resolved = self.resolver.resolve(
            "TSW_PORTAINER_ADMIN_PASSWORD",
            operator_value="operator-value",
        )

        self.assertEqual(CredentialSource.OPERATOR, resolved.source)
        self.assertEqual("operator-value", resolved.value)

    def test_blank_candidates_fall_back_to_catalog_default(self):
        resolved = self.resolver.resolve(
            "TSW_PORTAINER_ADMIN_PASSWORD",
            operator_value="   ",
            secure_value="\t",
        )

        self.assertEqual(CredentialSource.DEFAULT, resolved.source)

    def test_available_vault_value_has_highest_precedence_after_bootstrap(self):
        resolved = self.resolver.resolve(
            "TSW_PORTAINER_ADMIN_PASSWORD",
            operator_value="operator-value",
            secure_value="vault-value",
            secure_source=SecureCredentialSource.SELF_HOSTED_INFISICAL,
            phase=CredentialResolutionPhase.POST_BOOTSTRAP,
        )

        self.assertEqual(CredentialSource.VAULT, resolved.source)
        self.assertEqual("vault-value", resolved.value)

    def test_external_vault_value_can_be_used_during_bootstrap_when_identified(self):
        resolved = self.resolver.resolve(
            "TSW_PORTAINER_ADMIN_PASSWORD",
            operator_value="operator-value",
            secure_value="external-value",
            secure_source=SecureCredentialSource.EXTERNAL_INFISICAL,
            phase=CredentialResolutionPhase.BOOTSTRAP,
        )

        self.assertEqual(CredentialSource.VAULT, resolved.source)
        self.assertEqual("external-value", resolved.value)

    def test_self_hosted_vault_value_is_rejected_before_bootstrap(self):
        with self.assertRaisesRegex(CredentialResolutionError, "cannot provide"):
            self.resolver.resolve(
                "TSW_PORTAINER_ADMIN_PASSWORD",
                secure_value="self-hosted-value",
                secure_source=SecureCredentialSource.SELF_HOSTED_INFISICAL,
                phase=CredentialResolutionPhase.BOOTSTRAP,
            )

    def test_secure_value_requires_explicit_source_identity(self):
        with self.assertRaisesRegex(CredentialResolutionError, "must be identified"):
            self.resolver.resolve(
                "TSW_PORTAINER_ADMIN_PASSWORD",
                secure_value="unclassified-value",
            )

    def test_unknown_key_fails_when_no_override_exists(self):
        with self.assertRaisesRegex(CredentialResolutionError, "No credential default"):
            self.resolver.resolve("TSW_UNKNOWN_PASSWORD")

    def test_resolve_many_and_source_metadata_are_value_free(self):
        snapshot = CredentialResolutionService(self.resolver).resolve_post_bootstrap(
            ("TSW_PORTAINER_ADMIN_PASSWORD", "TSW_JENKINS_ADMIN_PASSWORD"),
            operator_values={"TSW_JENKINS_ADMIN_PASSWORD": "operator-value"},
        )
        encoded = snapshot.source_metadata()
        decoded = decode_source_metadata(encoded)

        self.assertEqual(CredentialSource.DEFAULT, decoded["TSW_PORTAINER_ADMIN_PASSWORD"])
        self.assertEqual(CredentialSource.OPERATOR, decoded["TSW_JENKINS_ADMIN_PASSWORD"])
        self.assertNotIn(INTERNAL_TEST_PASSWORD, encoded)
        self.assertNotIn(CREDENTIAL_SOURCE_MAP_ENVIRONMENT, encoded)

    def test_source_metadata_rejects_invalid_payloads(self):
        for payload in ([], {"OTHER": "default"}, {"TSW_KEY": "unsupported"}):
            with self.subTest(payload=payload):
                with self.assertRaises(CredentialResolutionError):
                    decode_source_metadata(json.dumps(payload))

        with self.assertRaises(CredentialResolutionError):
            decode_source_metadata("not-json")

    def test_rerun_resolution_is_deterministic(self):
        first = self.resolver.resolve_many(("TSW_PORTAINER_ADMIN_PASSWORD",))
        second = self.resolver.resolve_many(("TSW_PORTAINER_ADMIN_PASSWORD",))

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
