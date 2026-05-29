import unittest
from tests.support.async_helpers import async_checkpoint

from tiny_swarm_world.domain.inventory import VerificationStatus
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    ManagedLxcBackendSelection,
    NodeProviderKind,
    NodeRole,
    NodeSpec,
    ProviderSelection,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import (
    LxcNodeCommandResult,
    LxcNodeProvider,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    LegacyProviderFallback,
    NodeProviderConfig,
    NodeProviderNodeConfig,
    NodeProviderProfileRequirement,
    ProviderVerificationMetadata,
)


class TestLxcNodeProvider(unittest.IsolatedAsyncioTestCase):
    async def test_missing_node_launches_incus_container_and_verifies_created(self):
        runner = _FakeRunner(
            _profile(),
            _list(),
            _ok(),
            _list(_node("swarm-manager", "Running")),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("created", result.evidence["lifecycle_outcome"])
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (
                    (
                        "incus",
                        "launch",
                        "ubuntu:24.04",
                        "swarm-manager",
                        "--profile",
                        "docker-swarm",
                        "-c",
                        "user.tiny_swarm_world.managed=true",
                        "-c",
                        "user.tiny_swarm_world.node=swarm-manager",
                        "-c",
                        "user.tiny_swarm_world.image_alias=ubuntu-24.04",
                        "-c",
                        "limits.cpu=2",
                        "-c",
                        "limits.memory=4GiB",
                        "-d",
                        "root,size=20GiB",
                    ),
                    300.0,
                ),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_missing_node_blocks_without_live_mutation_consent(self):
        runner = _FakeRunner(
            _profile(),
            _list(),
        )
        provider = _provider(runner, allow_live_mutation=False)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("live_mutation_consent_missing", result.evidence["classification"])
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_existing_running_lxd_node_is_already_present_without_launch(self):
        runner = _FakeRunner(
            _profile(),
            _list(_node("swarm-manager", "Running")),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.LXD))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("already_present", result.evidence["lifecycle_outcome"])
        self.assertEqual(
            [
                (("lxc", "profile", "show", "docker-swarm"), 5.0),
                (("lxc", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_existing_stopped_node_is_started_then_verified(self):
        runner = _FakeRunner(
            _profile(),
            _list(_node("swarm-manager", "Stopped")),
            _ok(),
            _list(_node("swarm-manager", "Running")),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("started", result.evidence["lifecycle_outcome"])
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (("incus", "start", "swarm-manager"), 60.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_blocked_selection_returns_blocked_without_config_or_runner_calls(self):
        repository = _FakeConfigRepository(_config())
        runner = _FakeRunner()
        provider = LxcNodeProvider(config_repository=repository, runner=runner)

        result = await provider.ensure_node(
            _node_spec(),
            ProviderSelection.from_lxc_backend_selection(
                ManagedLxcBackendSelection.missing(
                    remediation=("Install a managed LXC backend.",),
                )
            ),
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("provider_selection_blocked", result.evidence["classification"])
        self.assertEqual(0, repository.load_count)
        self.assertEqual([], runner.calls)
        self.assertEvidenceIsSummaryOnly(result)

    async def test_existing_unmanaged_node_blocks_before_start_or_verify_success(self):
        runner = _FakeRunner(
            _profile(),
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    config={"user.tiny_swarm_world.managed": "false"},
                )
            ),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("existing_node_not_managed", result.evidence["classification"])
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_unsafe_provider_profile_blocks_before_node_lookup_or_launch(self):
        runner = _FakeRunner(
            _profile(config={"security.privileged": "true"}),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("unsafe_provider_profile", result.evidence["classification"])
        self.assertEqual(
            [(("incus", "profile", "show", "docker-swarm"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_passthrough_provider_profile_device_blocks_before_node_lookup(self):
        runner = _FakeRunner(
            _profile(devices={"gpu0": {"type": "gpu"}}),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("unsafe_provider_profile", result.evidence["classification"])
        self.assertEqual(
            [(("incus", "profile", "show", "docker-swarm"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_profile_missing_blocks_before_node_lookup_or_launch(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(
                returncode=1,
                stderr="permission denied for alice at /home/alice",
            )
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("profile_missing", result.evidence["classification"])
        self.assertEqual(
            [(("incus", "profile", "show", "docker-swarm"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_launch_failure_maps_to_failed_to_apply_without_raw_output(self):
        runner = _FakeRunner(
            _profile(),
            _list(),
            LxcNodeCommandResult(
                returncode=2,
                stdout="token=secret",
                stderr="failed under /home/alice",
            ),
            _list(),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual("launch_failed", result.evidence["classification"])
        self.assertEqual("2", result.evidence["return_code"])
        self.assertEvidenceIsSummaryOnly(result)

    async def test_apply_success_with_missing_verify_maps_to_failed_to_verify(self):
        runner = _FakeRunner(
            _profile(),
            _list(),
            _ok(),
            _list(),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual("created_node_not_verified", result.evidence["classification"])
        self.assertEvidenceIsSummaryOnly(result)

    async def test_unsafe_resource_config_blocks_before_runner_calls(self):
        runner = _FakeRunner()
        provider = _provider(
            runner,
            config=_config(resources={"cpu": "2", "memory": "4G", "disk": "20G", "raw": "true"}),
        )

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("unsupported_resource_config", result.evidence["classification"])
        self.assertEqual([], runner.calls)

    async def test_backend_mismatch_blocks_before_runner_calls(self):
        runner = _FakeRunner()
        provider = _provider(runner)

        result = await provider.ensure_node(
            _node_spec(backend=ManagedLxcBackend.LXD),
            _selection(ManagedLxcBackend.INCUS),
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("node_backend_mismatch", result.evidence["classification"])
        self.assertEqual([], runner.calls)

    def test_timeouts_must_be_positive(self):
        with self.assertRaises(ValueError):
            LxcNodeProvider(
                config_repository=_FakeConfigRepository(_config()),
                runner=_FakeRunner(),
                launch_timeout_seconds=0,
            )
        with self.assertRaises(ValueError):
            LxcNodeProvider(
                config_repository=_FakeConfigRepository(_config()),
                runner=_FakeRunner(),
                start_timeout_seconds=0,
            )

    def assertEvidenceIsSummaryOnly(self, result):
        rendered = repr(result.to_dict()).casefold()
        forbidden_fragments = (
            "/home/",
            "stdout",
            "stderr",
            "token",
            "secret",
            "permission denied",
            "incus launch",
            "lxc launch",
            "incus start",
            "lxc start",
            "command",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, rendered)


class _FakeRunner:
    def __init__(self, *results: LxcNodeCommandResult):
        self.results = list(results)
        self.calls: list[tuple[tuple[str, ...], float]] = []

    async def run(
        self,
        args,
        timeout_seconds,
    ) -> LxcNodeCommandResult:
        await async_checkpoint()
        self.calls.append((tuple(args), timeout_seconds))
        _assert_safe_lifecycle_command(args)
        if not self.results:
            raise AssertionError("unexpected LXC lifecycle call")
        return self.results.pop(0)


class _FakeConfigRepository:
    def __init__(self, config: NodeProviderConfig):
        self.config = config
        self.load_count = 0

    def load(self) -> NodeProviderConfig:
        self.load_count += 1
        return self.config


def _provider(
    runner: _FakeRunner,
    *,
    config: NodeProviderConfig | None = None,
    allow_live_mutation: bool = True,
) -> LxcNodeProvider:
    return LxcNodeProvider(
        config_repository=_FakeConfigRepository(config or _config()),
        runner=runner,
        allow_live_mutation=allow_live_mutation,
    )


def _selection(backend: ManagedLxcBackend) -> ProviderSelection:
    return ProviderSelection.from_lxc_backend_selection(
        ManagedLxcBackendSelection.for_backend(backend)
    )


def _node_spec(backend: ManagedLxcBackend | None = None) -> NodeSpec:
    return NodeSpec(
        name="swarm-manager",
        role=NodeRole.MANAGER,
        provider=NodeProviderKind.LXC_NATIVE,
        backend=backend,
    )


def _config(
    *,
    resources: dict[str, str] | None = None,
) -> NodeProviderConfig:
    return NodeProviderConfig(
        schema_version="1",
        default_provider=NodeProviderKind.LXC_NATIVE,
        preferred_backend=None,
        backend_candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
        legacy_fallbacks=(
            LegacyProviderFallback(
                provider=NodeProviderKind.MULTIPASS_LEGACY,
                selection_policy="explicit_only",
                automatic=False,
            ),
        ),
        nodes=(
            NodeProviderNodeConfig(
                spec=_node_spec(),
                profile="docker-swarm",
                image_alias="ubuntu-24.04",
                resources=resources or {"cpu": "2", "memory": "4GiB", "disk": "20GiB"},
                networks=("control",),
            ),
        ),
        profiles=(
            NodeProviderProfileRequirement(
                name="docker-swarm",
                backend_support=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
                risk_labels=("docker_in_container_requires_nesting",),
                privileged_default=False,
                nesting_required=True,
                syscall_interception_required=True,
                cgroup_policy="v2_required",
                apparmor_policy="provider_default",
                seccomp_policy="provider_default",
                capability_additions=(),
                host_network=False,
                host_mounts=(),
                live_mutation_consent_required=True,
                blocks_mutation_when_missing=True,
            ),
        ),
        verification_metadata=ProviderVerificationMetadata(
            readiness_timeout_seconds=5,
            evidence_summary_only=True,
            store_raw_output=False,
            checks=("backend_readiness", "profile_requirements"),
        ),
    )


def _ok() -> LxcNodeCommandResult:
    return LxcNodeCommandResult(returncode=0, stdout="ok")


def _profile(
    *,
    config: dict[str, str] | None = None,
    devices: dict[str, dict[str, str]] | None = None,
) -> LxcNodeCommandResult:
    import json

    return LxcNodeCommandResult(
        returncode=0,
        stdout=json.dumps(
            {
                "name": "docker-swarm",
                "config": config or {},
                "devices": devices or {},
            }
        ),
    )


def _list(*nodes: dict[str, object]) -> LxcNodeCommandResult:
    import json

    return LxcNodeCommandResult(returncode=0, stdout=json.dumps(list(nodes)))


def _node(
    name: str,
    status: str,
    *,
    config: dict[str, str] | None = None,
    profiles: tuple[str, ...] = ("docker-swarm",),
    devices: dict[str, dict[str, str]] | None = None,
) -> dict[str, object]:
    marker_config = {
        "user.tiny_swarm_world.managed": "true",
        "user.tiny_swarm_world.node": name,
        "user.tiny_swarm_world.image_alias": "ubuntu-24.04",
    }
    marker_config.update(config or {})
    return {
        "name": name,
        "status": status,
        "type": "container",
        "profiles": list(profiles),
        "config": marker_config,
        "devices": devices or {},
    }


def _assert_safe_lifecycle_command(args) -> None:
    argv = tuple(args)
    if not argv or argv[0] not in {"incus", "lxc"}:
        raise AssertionError(f"unexpected provider executable: {argv!r}")
    if any(not isinstance(item, str) for item in argv):
        raise AssertionError(f"provider argv must contain strings only: {argv!r}")
    if any(
        token in {"delete", "remove", "restart", "stop", "exec", "config", "network"}
        for token in argv
    ):
        raise AssertionError(f"unsafe provider command was called: {argv!r}")
    allowed_shapes = {
        ("incus", "profile", "show"),
        ("lxc", "profile", "show"),
        ("incus", "list"),
        ("lxc", "list"),
        ("incus", "launch"),
        ("lxc", "launch"),
        ("incus", "start"),
        ("lxc", "start"),
    }
    shape = argv[:3] if argv[:2] in {("incus", "profile"), ("lxc", "profile")} else argv[:2]
    if shape not in allowed_shapes:
        raise AssertionError(f"unexpected provider command was called: {argv!r}")


if __name__ == "__main__":
    unittest.main()
