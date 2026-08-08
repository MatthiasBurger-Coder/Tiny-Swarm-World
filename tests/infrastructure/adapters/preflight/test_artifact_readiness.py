import unittest
from unittest.mock import MagicMock

from tiny_swarm_world.domain.preflight import ReadinessCheckResult, ReadinessProbeRequest, ReadinessStatus
from tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness import (
    ARTIFACT_READINESS_TARGETS,
    BoundedArtifactReadinessAdapter,
    DockerManagerReadinessProbe,
    HttpEndpointReadinessProbe,
)


class TestArtifactReadiness(unittest.TestCase):
    def test_all_required_targets_are_explicit_and_receive_bounded_request(self):
        calls = []

        def ready(request):
            calls.append(request)
            return ReadinessCheckResult(
                target_id=request.target_id,
                status=ReadinessStatus.READY,
                message="Readiness check passed.",
                remediation="No remediation required.",
                evidence={"evidence_scope": "live"},
            )

        adapter = BoundedArtifactReadinessAdapter(
            {target: ready for target in ARTIFACT_READINESS_TARGETS}
        )
        for target in ARTIFACT_READINESS_TARGETS:
            result = adapter.check(
                ReadinessProbeRequest(target_id=target, timeout_seconds=2.0, max_attempts=2)
            )
            self.assertTrue(result.ready)

        self.assertEqual(len(ARTIFACT_READINESS_TARGETS), len(calls))
        self.assertTrue(all(call.timeout_seconds == 2.0 for call in calls))
        self.assertTrue(all(call.max_attempts == 2 for call in calls))

    def test_timeout_unavailable_and_unknown_remain_distinct(self):
        adapter = BoundedArtifactReadinessAdapter(
            {
                target: (
                    (lambda _request: (_ for _ in ()).throw(TimeoutError()))
                    if target == "docker:manager"
                    else (lambda _request: (_ for _ in ()).throw(ConnectionError()))
                    if target == "registry:endpoint"
                    else lambda request: ReadinessCheckResult(
                        target_id=request.target_id,
                        status=ReadinessStatus.READY,
                        message="Readiness check passed.",
                        remediation="No remediation required.",
                        evidence={"evidence_scope": "live"},
                    )
                )
                for target in ARTIFACT_READINESS_TARGETS
            }
        )
        def request(target: str) -> ReadinessProbeRequest:
            return ReadinessProbeRequest(target_id=target)

        self.assertEqual(ReadinessStatus.TIMED_OUT, adapter.check(request("docker:manager")).status)
        self.assertEqual(ReadinessStatus.UNAVAILABLE, adapter.check(request("registry:endpoint")).status)
        self.assertEqual(ReadinessStatus.READY, adapter.check(request("nexus:endpoint")).status)
        self.assertEqual(
            ReadinessStatus.UNKNOWN,
            adapter.check(request("unknown:target")).status,
        )

    def test_http_probe_passes_timeout_and_does_not_store_response_body(self):
        response = MagicMock(status=401)
        opener = MagicMock(return_value=response)
        probe = HttpEndpointReadinessProbe(
            "https://registry.example.invalid/v2/",
            opener=opener,
            probe_kind="registry_endpoint",
        )

        result = probe(ReadinessProbeRequest(target_id="registry:endpoint", timeout_seconds=1.5))

        self.assertEqual(ReadinessStatus.READY, result.status)
        opener.assert_called_once_with("https://registry.example.invalid/v2/", timeout=1.5)
        self.assertNotIn("body", repr(result.to_dict()).lower())

    def test_docker_probe_uses_injected_runner_without_running_docker(self):
        runner = MagicMock(return_value=0)
        probe = DockerManagerReadinessProbe(runner=runner)

        result = probe(ReadinessProbeRequest(target_id="docker:manager", timeout_seconds=1.25))

        self.assertEqual(ReadinessStatus.READY, result.status)
        runner.assert_called_once_with(1.25)


if __name__ == "__main__":
    unittest.main()
