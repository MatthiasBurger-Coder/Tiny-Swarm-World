import unittest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from tiny_swarm_world.application.services.platform import NodeProviderSelectionRequest
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    NodeProviderKind,
)
from tiny_swarm_world.domain.preflight import ReadinessCheckResult, ReadinessProbeRequest, ReadinessStatus
from tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness import (
    ARTIFACT_READINESS_TARGETS,
    BoundedArtifactReadinessAdapter,
    DockerManagerReadinessProbe,
    HttpEndpointReadinessProbe,
    ManagedLxcDirectoryReadinessProbe,
    ManagedLxcDockerManagerReadinessProbe,
    LocalDirectoryReadinessProbe,
    UnavailableArtifactReadinessProbe,
)
from tiny_swarm_world.infrastructure.composition_runtime import (
    _artifact_readiness_backend,
    _build_artifact_readiness_gate,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


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

    def test_managed_docker_probe_executes_inside_manager_with_timeout(self):
        runner = MagicMock(return_value=0)
        probe = ManagedLxcDockerManagerReadinessProbe(
            ManagedLxcBackend.INCUS,
            runner=runner,
        )

        result = probe(
            ReadinessProbeRequest(target_id="docker:manager", timeout_seconds=1.25)
        )

        self.assertEqual(ReadinessStatus.READY, result.status)
        runner.assert_called_once_with(
            ("docker", "info", "--format", "{{.ServerVersion}}"),
            1.25,
        )
        self.assertNotIn("stdout", repr(result.to_dict()).lower())
        self.assertNotIn("stderr", repr(result.to_dict()).lower())

    def test_managed_storage_probe_executes_inside_manager_not_on_host(self):
        runner = MagicMock(return_value=0)
        probe = ManagedLxcDirectoryReadinessProbe(
            ManagedLxcBackend.INCUS,
            "/var/lib/docker",
            runner=runner,
        )

        result = probe(
            ReadinessProbeRequest(target_id="storage:manager", timeout_seconds=2.0)
        )

        self.assertEqual(ReadinessStatus.READY, result.status)
        runner.assert_called_once_with(("test", "-d", "/var/lib/docker"), 2.0)
        self.assertNotIn("path", result.evidence)

    def test_managed_probe_timeout_is_typed_and_redacted(self):
        secret_output = "token=do-not-report"
        timeout = subprocess.TimeoutExpired(
            ("incus", "exec", "swarm-manager"),
            0.5,
            output=secret_output,
            stderr=secret_output,
        )
        timed_out = MagicMock(side_effect=timeout)
        probes = {
            target: (
                ManagedLxcDockerManagerReadinessProbe(
                    ManagedLxcBackend.INCUS,
                    runner=timed_out,
                )
                if target == "docker:manager"
                else lambda request: ReadinessCheckResult(
                    target_id=request.target_id,
                    status=ReadinessStatus.READY,
                    message="Readiness check passed.",
                    remediation="No remediation required.",
                )
            )
            for target in ARTIFACT_READINESS_TARGETS
        }

        result = BoundedArtifactReadinessAdapter(probes).check(
            ReadinessProbeRequest(target_id="docker:manager", timeout_seconds=0.5)
        )

        self.assertEqual(ReadinessStatus.TIMED_OUT, result.status)
        self.assertNotIn(secret_output, repr(result.to_dict()))

    def test_managed_probe_missing_cli_and_nonzero_are_typed(self):
        missing = MagicMock(side_effect=FileNotFoundError("incus secret path"))
        failed = MagicMock(return_value=3)

        missing_result = _adapter_with_managed_docker(missing).check(
            ReadinessProbeRequest(target_id="docker:manager")
        )
        failed_result = _adapter_with_managed_docker(failed).check(
            ReadinessProbeRequest(target_id="docker:manager")
        )

        self.assertEqual(ReadinessStatus.UNAVAILABLE, missing_result.status)
        self.assertEqual(ReadinessStatus.FAILED, failed_result.status)
        self.assertNotIn("secret path", repr(missing_result.to_dict()))

    @patch("tiny_swarm_world.infrastructure.adapters.preflight.artifact_readiness.subprocess.run")
    def test_managed_command_uses_selected_backend_and_discards_output(self, run):
        run.return_value.returncode = 0
        probe = ManagedLxcDockerManagerReadinessProbe(ManagedLxcBackend.LXD)

        result = probe(ReadinessProbeRequest(target_id="docker:manager"))

        self.assertEqual(ReadinessStatus.READY, result.status)
        run.assert_called_once_with(
            (
                "lxc",
                "exec",
                "swarm-manager",
                "--",
                "docker",
                "info",
                "--format",
                "{{.ServerVersion}}",
            ),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
            timeout=5.0,
        )

    def test_composition_selects_managed_backend_from_provider_request(self):
        self.assertEqual(
            ManagedLxcBackend.LXD,
            _artifact_readiness_backend(
                NodeProviderSelectionRequest(
                    preferred_backend=ManagedLxcBackend.LXD,
                )
            ),
        )
        self.assertEqual(
            ManagedLxcBackend.INCUS,
            _artifact_readiness_backend(
                NodeProviderSelectionRequest(
                    backend_candidates=(ManagedLxcBackend.INCUS,),
                )
            ),
        )
        self.assertIsNone(
            _artifact_readiness_backend(
                NodeProviderSelectionRequest(
                    requested_provider=NodeProviderKind.UNSUPPORTED,
                )
            )
        )

    def test_empty_lxc_backend_selection_fails_closed_without_host_substitution(self):
        request = NodeProviderSelectionRequest(backend_candidates=())

        with tempfile.TemporaryDirectory() as directory:
            gate = _build_artifact_readiness_gate(
                ProjectPaths.from_roots(Path(directory)),
                request,
            )

        probes = gate.readiness._probes
        self.assertIsInstance(
            probes["docker:manager"],
            UnavailableArtifactReadinessProbe,
        )
        self.assertIsInstance(
            probes["storage:manager"],
            UnavailableArtifactReadinessProbe,
        )
        self.assertIsInstance(probes["build:inputs"], LocalDirectoryReadinessProbe)
        self.assertEqual(
            ReadinessStatus.UNAVAILABLE,
            gate.readiness.check(ReadinessProbeRequest(target_id="docker:manager")).status,
        )
        self.assertEqual(
            ReadinessStatus.UNAVAILABLE,
            gate.readiness.check(ReadinessProbeRequest(target_id="storage:manager")).status,
        )

    def test_non_managed_provider_keeps_local_manager_probes(self):
        request = NodeProviderSelectionRequest(
            requested_provider=NodeProviderKind.UNSUPPORTED,
        )

        with tempfile.TemporaryDirectory() as directory:
            gate = _build_artifact_readiness_gate(
                ProjectPaths.from_roots(Path(directory)),
                request,
            )

        probes = gate.readiness._probes
        self.assertIsInstance(probes["docker:manager"], DockerManagerReadinessProbe)
        self.assertIsInstance(probes["storage:manager"], LocalDirectoryReadinessProbe)
        self.assertIsInstance(probes["build:inputs"], LocalDirectoryReadinessProbe)

    @patch("tiny_swarm_world.infrastructure.composition_runtime.shutil.which", return_value=None)
    def test_ambiguous_lxc_backends_without_cli_fail_closed(self, _which):
        request = NodeProviderSelectionRequest(
            backend_candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
        )

        with tempfile.TemporaryDirectory() as directory:
            gate = _build_artifact_readiness_gate(
                ProjectPaths.from_roots(Path(directory)),
                request,
            )

        probes = gate.readiness._probes
        self.assertNotIsInstance(probes["docker:manager"], DockerManagerReadinessProbe)
        self.assertNotIsInstance(probes["storage:manager"], LocalDirectoryReadinessProbe)
        self.assertIsInstance(probes["build:inputs"], LocalDirectoryReadinessProbe)
        self.assertEqual(
            ReadinessStatus.UNAVAILABLE,
            gate.readiness.check(ReadinessProbeRequest(target_id="docker:manager")).status,
        )
        self.assertEqual(
            ReadinessStatus.UNAVAILABLE,
            gate.readiness.check(ReadinessProbeRequest(target_id="storage:manager")).status,
        )


def _adapter_with_managed_docker(runner):
    return BoundedArtifactReadinessAdapter(
        {
            target: (
                ManagedLxcDockerManagerReadinessProbe(
                    ManagedLxcBackend.INCUS,
                    runner=runner,
                )
                if target == "docker:manager"
                else lambda request: ReadinessCheckResult(
                    target_id=request.target_id,
                    status=ReadinessStatus.READY,
                    message="Readiness check passed.",
                    remediation="No remediation required.",
                )
            )
            for target in ARTIFACT_READINESS_TARGETS
        }
    )


if __name__ == "__main__":
    unittest.main()
