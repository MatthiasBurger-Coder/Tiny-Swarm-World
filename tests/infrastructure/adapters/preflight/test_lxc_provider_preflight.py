import unittest

from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    ManagedLxcBackendSelectionStatus,
    NodeProviderKind,
    ProviderReadinessStatus,
)
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
)
from tiny_swarm_world.infrastructure.adapters.preflight import LxcProviderPreflightProbe
from tiny_swarm_world.infrastructure.adapters.preflight.lxc_provider_preflight import (
    LxcProviderProbeResult,
)


class TestLxcProviderPreflightProbe(unittest.IsolatedAsyncioTestCase):
    async def test_missing_lxd_and_incus_executables_returns_backend_missing_without_probe(self):
        runner = _FakeRunner()

        readiness = await _probe(available=(), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.BACKEND_MISSING, readiness.status)
        self.assertEqual(ManagedLxcBackendSelectionStatus.MISSING, readiness.backend_selection.status)
        self.assertTrue(readiness.blocks_mutation)
        self.assertEqual([], runner.calls)
        self.assertEqual("absent", readiness.backend_selection.evidence["incus_cli"])
        self.assertEqual("absent", readiness.backend_selection.evidence["lxd_cli"])

    async def test_ready_incus_backend_uses_version_and_info_with_timeout(self):
        runner = _FakeRunner(_ok(), _ok())

        readiness = await _probe(available=("incus",), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.READY, readiness.status)
        self.assertEqual(ManagedLxcBackend.INCUS, readiness.backend_selection.backend)
        self.assertEqual(
            [
                (("incus", "version"), 5.0),
                (("incus", "info"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(readiness)

    async def test_ready_lxd_backend_uses_version_and_info_with_timeout(self):
        runner = _FakeRunner(_ok(), _ok())

        readiness = await _probe(available=("lxc",), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.READY, readiness.status)
        self.assertEqual(ManagedLxcBackend.LXD, readiness.backend_selection.backend)
        self.assertEqual(
            [
                (("lxc", "version"), 5.0),
                (("lxc", "info"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(readiness)

    async def test_timeout_maps_to_timeout_without_raw_output(self):
        runner = _FakeRunner(
            LxcProviderProbeResult(
                returncode=124,
                stdout="token=abc /home/example",
                stderr="10.0.0.1",
                timed_out=True,
            )
        )

        readiness = await _probe(available=("incus",), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.TIMEOUT, readiness.status)
        self.assertEqual("timeout", readiness.evidence["classification_source"])
        self.assertEvidenceIsSummaryOnly(readiness)

    async def test_info_daemon_unavailable_maps_to_daemon_unavailable(self):
        runner = _FakeRunner(
            _ok(),
            LxcProviderProbeResult(
                returncode=2,
                stderr="cannot connect to unix socket /var/snap/lxd/common/lxd/unix.socket",
            ),
        )

        readiness = await _probe(available=("lxc",), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.DAEMON_UNAVAILABLE, readiness.status)
        self.assertEqual(ManagedLxcBackend.LXD, readiness.backend_selection.backend)
        self.assertEvidenceIsSummaryOnly(readiness)

    async def test_info_permission_denied_maps_to_permission_denied(self):
        runner = _FakeRunner(
            _ok(),
            LxcProviderProbeResult(
                returncode=1,
                stderr="permission denied for user alice",
            ),
        )

        readiness = await _probe(available=("incus",), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.PERMISSION_DENIED, readiness.status)
        self.assertIn("access", " ".join(readiness.remediation))
        self.assertEvidenceIsSummaryOnly(readiness)
        self.assertNotIn("alice", repr(readiness.to_dict()).casefold())

    async def test_unknown_nonzero_failure_is_summary_only(self):
        runner = _FakeRunner(
            _ok(),
            LxcProviderProbeResult(
                returncode=9,
                stderr="unexpected /home/example failure for 10.0.0.2",
            ),
        )

        readiness = await _probe(available=("incus",), runner=runner).provider_readiness(
            NodeProviderKind.LXC_NATIVE
        )

        self.assertEqual(ProviderReadinessStatus.UNKNOWN_FAILURE, readiness.status)
        self.assertEvidenceIsSummaryOnly(readiness)

    async def test_both_backends_ready_without_preference_is_ambiguous(self):
        runner = _FakeRunner(_ok(), _ok(), _ok(), _ok())

        readiness = await _probe(
            available=("incus", "lxc"),
            runner=runner,
        ).provider_readiness(NodeProviderKind.LXC_NATIVE)

        self.assertEqual(ProviderReadinessStatus.BACKEND_AMBIGUOUS, readiness.status)
        self.assertEqual(ManagedLxcBackendSelectionStatus.AMBIGUOUS, readiness.backend_selection.status)
        self.assertEqual(
            (ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
            readiness.backend_selection.candidates,
        )
        self.assertNotIn("multipass", repr(readiness.to_dict()).casefold())

    async def test_preferred_backend_resolves_ambiguous_availability(self):
        runner = _FakeRunner(_ok(), _ok())

        readiness = await _probe(
            available=("incus", "lxc"),
            runner=runner,
        ).provider_readiness(
            NodeProviderKind.LXC_NATIVE,
            preferred_backend=ManagedLxcBackend.LXD,
        )

        self.assertEqual(ProviderReadinessStatus.READY, readiness.status)
        self.assertEqual(ManagedLxcBackend.LXD, readiness.backend_selection.backend)
        self.assertEqual(
            [
                (("lxc", "version"), 5.0),
                (("lxc", "info"), 5.0),
            ],
            runner.calls,
        )

    async def test_wsl2_without_systemd_reports_systemd_unavailable(self):
        runner = _FakeRunner()

        readiness = await _probe(
            available=("incus",),
            runner=runner,
            host_environment=_wsl2_report(),
            systemd=False,
        ).provider_readiness(NodeProviderKind.LXC_NATIVE)

        self.assertEqual(ProviderReadinessStatus.SYSTEMD_UNAVAILABLE, readiness.status)
        self.assertEqual("wsl2", readiness.evidence["host_kind"])
        self.assertEqual("2", readiness.evidence["wsl_generation"])
        self.assertEqual("absent", readiness.evidence["systemd"])
        self.assertEqual([], runner.calls)

    async def test_wsl2_systemd_present_but_provider_daemon_unavailable_is_daemon_unavailable(self):
        runner = _FakeRunner(
            _ok(),
            LxcProviderProbeResult(
                returncode=2,
                stderr="daemon is not running",
            ),
        )

        readiness = await _probe(
            available=("incus",),
            runner=runner,
            host_environment=_wsl2_report(),
            systemd=True,
            wsl_capability=True,
        ).provider_readiness(NodeProviderKind.LXC_NATIVE)

        self.assertEqual(ProviderReadinessStatus.DAEMON_UNAVAILABLE, readiness.status)
        self.assertNotEqual(ProviderReadinessStatus.WSL_UNSUPPORTED, readiness.status)

    async def test_wsl2_missing_required_capability_reports_wsl_unsupported(self):
        runner = _FakeRunner()

        readiness = await _probe(
            available=("incus",),
            runner=runner,
            host_environment=_wsl2_report(),
            systemd=True,
            wsl_capability=False,
        ).provider_readiness(NodeProviderKind.LXC_NATIVE)

        self.assertEqual(ProviderReadinessStatus.WSL_UNSUPPORTED, readiness.status)
        self.assertEqual("unsupported", readiness.evidence["wsl_capability"])
        self.assertEqual([], runner.calls)

    async def test_sandbox_host_reports_host_unsupported_without_backend_probe(self):
        runner = _FakeRunner()

        readiness = await _probe(
            available=("incus",),
            runner=runner,
            host_environment=HostEnvironmentReport(
                environment=HostEnvironmentKind.SANDBOX_UNVERIFIED,
                setup_path=SetupPath.SANDBOX_UNVERIFIED,
                remediation=("Use static validation only.",),
                evidence={"classification": "sandbox_unverified"},
            ),
        ).provider_readiness(NodeProviderKind.LXC_NATIVE)

        self.assertEqual(ProviderReadinessStatus.HOST_UNSUPPORTED, readiness.status)
        self.assertEqual([], runner.calls)

    async def test_unsupported_provider_request_reports_unsupported(self):
        runner = _FakeRunner()

        readiness = await _probe(available=("incus",), runner=runner).provider_readiness(
            NodeProviderKind.MULTIPASS_LEGACY
        )

        self.assertEqual(ProviderReadinessStatus.UNSUPPORTED, readiness.status)
        self.assertEqual([], runner.calls)

    def assertEvidenceIsSummaryOnly(self, readiness):
        rendered = repr(readiness.to_dict()).casefold()
        forbidden_fragments = (
            "/home/",
            "/var/",
            "10.0.0.",
            "stdout",
            "stderr",
            "token",
            "sudo",
            "lxc info",
            "lxc version",
            "incus info",
            "incus version",
            "unix.socket",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, rendered)


class _FakeRunner:
    def __init__(self, *results: LxcProviderProbeResult):
        self.results = list(results)
        self.calls: list[tuple[tuple[str, ...], float]] = []

    async def run(
        self,
        args,
        timeout_seconds,
    ) -> LxcProviderProbeResult:
        self.calls.append((tuple(args), timeout_seconds))
        _assert_read_only_command(args)
        if not self.results:
            raise AssertionError("unexpected provider probe call")
        return self.results.pop(0)


def _probe(
    *,
    available: tuple[str, ...],
    runner: _FakeRunner,
    host_environment: HostEnvironmentReport | None = None,
    systemd: bool = True,
    wsl_capability: bool = True,
) -> LxcProviderPreflightProbe:
    available_set = set(available)
    return LxcProviderPreflightProbe(
        host_environment_provider=lambda: host_environment or _native_linux_report(),
        executable_available=lambda name: name in available_set,
        runner=runner,
        systemd_available=lambda: systemd,
        wsl_lxc_capability_available=lambda: wsl_capability,
    )


def _ok() -> LxcProviderProbeResult:
    return LxcProviderProbeResult(returncode=0, stdout="ok\n")


def _native_linux_report() -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=HostEnvironmentKind.NATIVE_LINUX,
        setup_path=SetupPath.NATIVE_LINUX,
        remediation=("Verify provider readiness before live setup.",),
        evidence={"classification": "native_linux"},
    )


def _wsl2_report() -> HostEnvironmentReport:
    return HostEnvironmentReport(
        environment=HostEnvironmentKind.WSL2,
        setup_path=SetupPath.WSL2,
        remediation=("Verify WSL2 provider readiness before live setup.",),
        evidence={
            "classification": "wsl2",
            "wsl_generation": "2",
        },
    )


def _assert_read_only_command(args) -> None:
    argv = tuple(args)
    self_mutating_tokens = {
        "config",
        "create",
        "delete",
        "edit",
        "exec",
        "import",
        "init",
        "launch",
        "network",
        "profile",
        "remove",
        "restart",
        "set",
        "start",
        "stop",
        "storage",
    }
    if any(token in self_mutating_tokens for token in argv):
        raise AssertionError(f"mutating provider command was called: {argv!r}")
    if argv not in {
        ("incus", "version"),
        ("incus", "info"),
        ("lxc", "version"),
        ("lxc", "info"),
    }:
        raise AssertionError(f"unexpected provider command was called: {argv!r}")


if __name__ == "__main__":
    unittest.main()
