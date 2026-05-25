import unittest

from tiny_swarm_world.application.services.deployment.verify_external_swarm_input import (
    VerifyExternalSwarmInput,
)
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestVerifyExternalSwarmInput(unittest.IsolatedAsyncioTestCase):
    async def test_verifies_declared_service_access_input_exists(self):
        runtime = _FakeSwarmRuntime(present=True)
        check = VerifyExternalSwarmInput(
            runtime,
            "tsw_vaultwarden_admin_token",
            source_ref="default",
        )

        verification = await check.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual("deployment:service-access-external-input", verification.target_id)
        self.assertEqual(["tsw_vaultwarden_admin_token"], runtime.requested_names)
        self.assertEqual("external_swarm_input", verification.evidence["resource_kind"])
        self.assertEqual("true", verification.evidence["resource_present"])
        self.assertEqual("default", verification.evidence["source_ref"])

    async def test_blocks_when_declared_input_is_missing(self):
        verification = await VerifyExternalSwarmInput(
            _FakeSwarmRuntime(present=False),
            "operator_defined_name",
            source_ref="operator_env",
        ).verify()

        self.assertEqual(VerificationStatus.BLOCKED, verification.status)
        self.assertEqual("false", verification.evidence["resource_present"])
        self.assertEqual("operator_env", verification.evidence["source_ref"])
        self.assertNotIn("operator_defined_name", str(verification.to_dict()))

    async def test_sanitizes_runtime_failure_without_sensitive_payload(self):
        verification = await VerifyExternalSwarmInput(
            _FakeSwarmRuntime(exception=RuntimeError("token=leaked")),
            "tsw_vaultwarden_admin_token",
        ).verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, verification.status)
        self.assertIn("RuntimeError", verification.message)
        self.assertNotIn("token", str(verification.to_dict()).casefold())


class _FakeSwarmRuntime:
    def __init__(
        self,
        *,
        present: bool = False,
        exception: Exception | None = None,
    ):
        self.present = present
        self.exception = exception
        self.requested_names: list[str] = []

    def external_secret_exists(self, name: str) -> bool:
        self.requested_names.append(name)
        if self.exception is not None:
            raise self.exception
        return self.present
