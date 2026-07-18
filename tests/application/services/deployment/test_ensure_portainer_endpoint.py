import unittest

from tiny_swarm_world.application.services.deployment import EnsurePortainerEndpoint
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsurePortainerEndpoint(unittest.IsolatedAsyncioTestCase):
    async def test_run_ensures_local_endpoint(self):
        client = _RecordingPortainerClient(endpoint_id=7)
        service = EnsurePortainerEndpoint(client, "local")

        await service.run()

        self.assertEqual(client.ensured_endpoint_names, ["local"])

    async def test_verify_reports_registered_endpoint(self):
        client = _RecordingPortainerClient(endpoint_id=7)
        service = EnsurePortainerEndpoint(client, "local")

        result = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(result.evidence["endpoint_state"], "registered")
        self.assertEqual(result.evidence["endpoint_ready"], "true")
        self.assertEqual(result.evidence["endpoint_id_present"], "true")

    async def test_verify_reports_failed_endpoint_lookup(self):
        client = _RecordingPortainerClient(endpoint_exception=RuntimeError("missing"))
        service = EnsurePortainerEndpoint(
            client,
            "local",
            max_attempts=1,
            wait_seconds=0,
        )

        result = await service.verify()

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(result.evidence["endpoint_state"], "unknown")
        self.assertEqual(result.evidence["endpoint_ready"], "false")

    async def test_run_retries_until_endpoint_registration_succeeds(self):
        client = _RetryPortainerClient(failures_before_success=2)
        service = EnsurePortainerEndpoint(
            client,
            "local",
            max_attempts=3,
            wait_seconds=0,
        )

        await service.run()

        self.assertEqual(client.call_count, 3)


class _RecordingPortainerClient:
    def __init__(
        self,
        *,
        endpoint_id: int = 0,
        endpoint_exception: Exception | None = None,
    ) -> None:
        self.endpoint_id = endpoint_id
        self.endpoint_exception = endpoint_exception
        self.ensured_endpoint_names: list[str] = []

    def ensure_local_endpoint(self, endpoint_name: str) -> int:
        self.ensured_endpoint_names.append(endpoint_name)
        return self.endpoint_id

    def get_endpoint_id_by_name(self, endpoint_name: str) -> int:
        if self.endpoint_exception is not None:
            raise self.endpoint_exception
        return self.endpoint_id


class _RetryPortainerClient:
    def __init__(self, *, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.call_count = 0

    def ensure_local_endpoint(self, endpoint_name: str) -> int:
        self.call_count += 1
        if self.call_count <= self.failures_before_success:
            raise RuntimeError("not ready")
        return 7
