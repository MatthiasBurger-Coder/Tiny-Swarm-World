import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests

from tiny_swarm_world.infrastructure.composition_probes import (
    EndpointReadinessCheck,
    _endpoint_status,
    _endpoint_status_ready,
    _linux_text_file_equals,
    _wsl_unprivileged_userns_clone_available,
)


class TestCompositionProbes(unittest.IsolatedAsyncioTestCase):
    def test_http_status_mapping_is_bounded_and_redirects_are_not_followed(self):
        session = MagicMock()
        session.get.return_value = SimpleNamespace(status_code=401)

        self.assertEqual(
            "http_401",
            _endpoint_status(session, "http://service/health", timeout_seconds=3),
        )
        session.get.assert_called_once_with(
            "http://service/health",
            timeout=3,
            allow_redirects=False,
        )
        self.assertTrue(_endpoint_status_ready("http_401"))
        self.assertTrue(_endpoint_status_ready("http_499"))
        self.assertFalse(_endpoint_status_ready("http_500"))
        self.assertFalse(_endpoint_status_ready("connection_error"))

    async def test_async_readiness_uses_injected_session_and_preserves_evidence(self):
        endpoint = SimpleNamespace(name="api", url="http://service/health")
        stack = SimpleNamespace(
            service_readiness_target_id="deployment:service-readiness",
            stack_name="service",
            endpoints=(endpoint,),
        )
        session = MagicMock()
        session.get.return_value = SimpleNamespace(status_code=200)
        check = EndpointReadinessCheck(
            stack,
            max_attempts=2,
            wait_seconds=0,
            timeout_seconds=2,
            session=session,
        )

        result = await check.verify_async()

        self.assertEqual("verified", result.status.value)
        self.assertEqual("verify", result.evidence["phase"])
        self.assertEqual("api=http_200", result.evidence["endpoint_statuses"])

    def test_endpoint_timeout_is_classified_without_raising(self):
        session = MagicMock()
        session.get.side_effect = requests.Timeout()

        self.assertEqual(
            "timeout",
            _endpoint_status(session, "http://service/health", timeout_seconds=1),
        )

    def test_missing_kernel_flag_is_fail_closed_and_does_not_read(self):
        path = MagicMock()
        path.exists.return_value = False

        with patch(
            "tiny_swarm_world.infrastructure.composition_probes._linux_text_file_equals",
            side_effect=AssertionError("missing flag must not be read"),
        ):
            self.assertTrue(_wsl_unprivileged_userns_clone_available(path))

    def test_kernel_flag_reader_handles_unreadable_files(self):
        path = MagicMock()
        path.exists.return_value = True
        path.read_text.side_effect = OSError("unreadable")

        self.assertFalse(_linux_text_file_equals(path, "1"))


if __name__ == "__main__":
    unittest.main()
