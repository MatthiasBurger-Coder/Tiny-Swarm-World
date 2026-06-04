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

    async def test_reset_managed_nodes_deletes_only_scoped_managed_nodes_and_verifies_absent(self):
        nodes = (_node_spec(), _node_spec(name="swarm-worker-1", role=NodeRole.WORKER))
        runner = _FakeTeardownRunner(
            _list(_node("swarm-manager", "Running")),
            _list(),
            _ok(),
            _list(),
        )
        provider = _provider(runner, config=_config(nodes=nodes))

        result = await provider.reset_nodes(nodes, _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("platform:reset:managed-nodes", result.target_id)
        self.assertEqual("managed_nodes_reset", result.evidence["classification"])
        self.assertEqual("2", result.evidence["expected_count"])
        self.assertEqual("2", result.evidence["verified_count"])
        self.assertEqual("true", result.evidence["applied"])
        self.assertEqual(
            [
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (("incus", "list", "swarm-worker-1", "--format", "json"), 5.0),
                (("incus", "delete", "swarm-manager", "--force"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_reset_preflights_all_nodes_before_any_delete(self):
        nodes = (_node_spec(), _node_spec(name="swarm-worker-1", role=NodeRole.WORKER))
        runner = _FakeTeardownRunner(
            _list(_node("swarm-manager", "Running")),
            _list(
                _node(
                    "swarm-worker-1",
                    "Running",
                    config={"user.tiny_swarm_world.managed": "false"},
                )
            ),
        )
        provider = _provider(runner, config=_config(nodes=nodes))

        result = await provider.reset_nodes(nodes, _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("managed_nodes_reset_blocked", result.evidence["classification"])
        self.assertEqual("2", result.evidence["expected_count"])
        self.assertEqual("1", result.evidence["planned_count"])
        self.assertEqual("1", result.evidence["blocked_count"])
        self.assertNotIn("applied", result.evidence)
        self.assertEqual(
            [
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (("incus", "list", "swarm-worker-1", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_destroy_managed_nodes_blocks_marker_mismatch_before_delete(self):
        runner = _FakeTeardownRunner(
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    config={"user.tiny_swarm_world.managed": "false"},
                )
            ),
        )
        provider = _provider(runner)

        result = await provider.destroy_nodes(
            (_node_spec(),),
            _selection(ManagedLxcBackend.INCUS),
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("platform:destroy:managed-nodes", result.target_id)
        self.assertEqual("managed_nodes_destroy_blocked", result.evidence["classification"])
        self.assertEqual(
            "destroy_existing_node_not_managed",
            result.evidence["first_failure_classification"],
        )
        self.assertEqual("1", result.evidence["blocked_count"])
        self.assertEqual(
            [(("incus", "list", "swarm-manager", "--format", "json"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_destroy_managed_nodes_treats_already_missing_nodes_as_verified(self):
        runner = _FakeTeardownRunner(_list())
        provider = _provider(runner)

        result = await provider.destroy_nodes(
            (_node_spec(),),
            _selection(ManagedLxcBackend.LXD),
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("managed_nodes_destroy", result.evidence["classification"])
        self.assertEqual("1", result.evidence["verified_count"])
        self.assertNotIn("applied", result.evidence)
        self.assertEqual(
            [(("lxc", "list", "swarm-manager", "--format", "json"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_reset_without_live_mutation_consent_never_deletes(self):
        runner = _FakeTeardownRunner(_list(_node("swarm-manager", "Running")))
        provider = _provider(runner, allow_live_mutation=False)

        result = await provider.reset_nodes(
            (_node_spec(),),
            _selection(ManagedLxcBackend.INCUS),
        )

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("managed_nodes_reset_blocked", result.evidence["classification"])
        self.assertEqual(
            "live_mutation_consent_missing",
            result.evidence["first_failure_classification"],
        )
        self.assertEqual(
            [(("incus", "list", "swarm-manager", "--format", "json"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_delete_failure_is_verified_when_scoped_lookup_is_already_absent(self):
        runner = _FakeTeardownRunner(
            _list(_node("swarm-manager", "Running")),
            LxcNodeCommandResult(
                returncode=1,
                stderr="instance disappeared under /home/alice",
            ),
            _list(),
        )
        provider = _provider(runner)

        result = await provider.reset_nodes(
            (_node_spec(),),
            _selection(ManagedLxcBackend.INCUS),
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("managed_nodes_reset", result.evidence["classification"])
        self.assertEqual("true", result.evidence["applied"])
        self.assertEqual(
            [
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (("incus", "delete", "swarm-manager", "--force"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_teardown_failure_evidence_is_summary_only(self):
        runner = _FakeTeardownRunner(
            _list(_node("swarm-manager", "Running")),
            LxcNodeCommandResult(
                returncode=2,
                stdout="token=secret",
                stderr="failed under /home/alice",
            ),
            _list(_node("swarm-manager", "Running")),
        )
        provider = _provider(runner)

        result = await provider.destroy_nodes(
            (_node_spec(),),
            _selection(ManagedLxcBackend.INCUS),
        )

        self.assertEqual(VerificationStatus.FAILED_TO_APPLY, result.status)
        self.assertEqual(
            "managed_nodes_destroy_apply_failed",
            result.evidence["classification"],
        )
        self.assertEqual(
            "destroy_delete_failed",
            result.evidence["first_failure_classification"],
        )
        self.assertEqual("1", result.evidence["failed_apply_count"])
        self.assertEqual("true", result.evidence["applied"])
        self.assertEvidenceIsSummaryOnly(result)

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
    def __init__(self, *results: LxcNodeCommandResult, command_guard=None):
        self.results = list(results)
        self.calls: list[tuple[tuple[str, ...], float]] = []
        self.command_guard = command_guard or _assert_safe_lifecycle_command

    async def run(
        self,
        args,
        timeout_seconds,
    ) -> LxcNodeCommandResult:
        await async_checkpoint()
        self.calls.append((tuple(args), timeout_seconds))
        self.command_guard(args)
        if not self.results:
            raise AssertionError("unexpected LXC lifecycle call")
        return self.results.pop(0)


class _FakeTeardownRunner(_FakeRunner):
    def __init__(self, *results: LxcNodeCommandResult):
        super().__init__(*results, command_guard=_assert_safe_teardown_command)


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


def _node_spec(
    backend: ManagedLxcBackend | None = None,
    *,
    name: str = "swarm-manager",
    role: NodeRole = NodeRole.MANAGER,
) -> NodeSpec:
    return NodeSpec(
        name=name,
        role=role,
        provider=NodeProviderKind.LXC_NATIVE,
        backend=backend,
    )


def _config(
    *,
    resources: dict[str, str] | None = None,
    nodes: tuple[NodeSpec, ...] | None = None,
) -> NodeProviderConfig:
    return NodeProviderConfig(
        schema_version="1",
        default_provider=NodeProviderKind.LXC_NATIVE,
        preferred_backend=None,
        backend_candidates=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
        nodes=tuple(
            NodeProviderNodeConfig(
                spec=node,
                profile="docker-swarm",
                image_alias="ubuntu-24.04",
                resources=resources or {"cpu": "2", "memory": "4GiB", "disk": "20GiB"},
                networks=("control",),
            )
            for node in (nodes or (_node_spec(),))
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


def _assert_safe_teardown_command(args) -> None:
    argv = tuple(args)
    if not argv or argv[0] not in {"incus", "lxc"}:
        raise AssertionError(f"unexpected provider executable: {argv!r}")
    if any(not isinstance(item, str) for item in argv):
        raise AssertionError(f"provider argv must contain strings only: {argv!r}")
    if argv[:2] in {("incus", "delete"), ("lxc", "delete")}:
        if len(argv) != 4 or argv[2] not in {
            "swarm-manager",
            "swarm-worker-1",
            "swarm-worker-2",
        } or argv[3] != "--force":
            raise AssertionError(f"unsafe provider delete was called: {argv!r}")
        return
    if argv[:2] in {("incus", "list"), ("lxc", "list")}:
        if len(argv) != 5 or argv[2] not in {
            "swarm-manager",
            "swarm-worker-1",
            "swarm-worker-2",
        } or argv[3:] != ("--format", "json"):
            raise AssertionError(f"unsafe provider list was called: {argv!r}")
        return
    raise AssertionError(f"unexpected provider teardown command was called: {argv!r}")


if __name__ == "__main__":
    unittest.main()
