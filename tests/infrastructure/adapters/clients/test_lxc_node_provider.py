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

    async def test_missing_manager_node_launches_with_manager_proxy_profile(self):
        runner = _FakeRunner(
            _profile(),
            _profile(name="docker-swarm-manager"),
            _list(),
            _ok(),
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    profiles=("docker-swarm", "docker-swarm-manager"),
                )
            ),
        )
        provider = _provider(
            runner,
            config=_config(additional_profiles=("docker-swarm-manager",)),
        )

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "profile", "show", "docker-swarm-manager"), 5.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (
                    (
                        "incus",
                        "launch",
                        "ubuntu:24.04",
                        "swarm-manager",
                        "--profile",
                        "docker-swarm",
                        "--profile",
                        "docker-swarm-manager",
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

    async def test_missing_manager_profile_is_created_before_launch(self):
        runner = _FakeRunner(
            _profile(),
            LxcNodeCommandResult(returncode=1, stderr="Profile not found"),
            _profile_list("default", "docker-swarm"),
            _ok(),
            _profile(name="docker-swarm-manager"),
            _list(),
            _ok(),
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    profiles=("docker-swarm", "docker-swarm-manager"),
                )
            ),
        )
        provider = _provider(
            runner,
            config=_config(additional_profiles=("docker-swarm-manager",)),
        )

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.LXD))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("created", result.evidence["lifecycle_outcome"])
        self.assertEqual("swarm-manager", result.evidence["node_name"])
        self.assertEqual(
            [
                (("lxc", "profile", "show", "docker-swarm"), 5.0),
                (("lxc", "profile", "show", "docker-swarm-manager"), 5.0),
                (("lxc", "profile", "list", "--format", "json"), 5.0),
                (("lxc", "profile", "create", "docker-swarm-manager"), 5.0),
                (("lxc", "profile", "show", "docker-swarm-manager"), 5.0),
                (("lxc", "list", "swarm-manager", "--format", "json"), 5.0),
                (
                    (
                        "lxc",
                        "launch",
                        "ubuntu:24.04",
                        "swarm-manager",
                        "--profile",
                        "docker-swarm",
                        "--profile",
                        "docker-swarm-manager",
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
                (("lxc", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_existing_swarm_profile_is_reconciled_without_using_node_name_as_profile(
        self,
    ):
        runner = _FakeRunner(
            _profile(config={}),
            _ok(),
            _ok(),
            _ok(),
            _profile(),
            _list(),
            _ok(),
            _list(_node("swarm-manager", "Running")),
        )
        provider = _provider(runner)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "profile", "set", "docker-swarm", "security.nesting", "true"), 5.0),
                (
                    (
                        "incus",
                        "profile",
                        "set",
                        "docker-swarm",
                        "security.syscalls.intercept.mknod",
                        "true",
                    ),
                    5.0,
                ),
                (
                    (
                        "incus",
                        "profile",
                        "set",
                        "docker-swarm",
                        "security.syscalls.intercept.setxattr",
                        "true",
                    ),
                    5.0,
                ),
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
        self.assertNotIn(
            ("incus", "profile", "show", "swarm-manager"),
            [call for call, _timeout in runner.calls],
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_manager_profile_accepts_expected_project_proxy_devices(self):
        runner = _FakeRunner(
            _profile(),
            _profile(name="docker-swarm-manager", devices=_project_proxy_devices()),
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    profiles=("docker-swarm", "docker-swarm-manager"),
                )
            ),
        )
        provider = _provider(
            runner,
            config=_config(additional_profiles=("docker-swarm-manager",)),
        )

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.LXD))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual("already_present", result.evidence["lifecycle_outcome"])
        self.assertEqual(
            [
                (("lxc", "profile", "show", "docker-swarm"), 5.0),
                (("lxc", "profile", "show", "docker-swarm-manager"), 5.0),
                (("lxc", "list", "swarm-manager", "--format", "json"), 5.0),
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
        self.assertEqual("managed_marker_not_true", result.evidence["mismatch_reasons"])
        self.assertEqual("different", result.evidence["observed_managed_marker"])
        self.assertEqual("matches", result.evidence["observed_node_marker"])
        self.assertEqual("matches", result.evidence["observed_image_alias_marker"])
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

    async def test_shared_provider_profile_proxy_device_blocks_before_node_lookup(self):
        runner = _FakeRunner(
            _profile(devices=_project_proxy_devices()),
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

    async def test_profile_missing_blocks_without_live_mutation_consent(self):
        runner = _FakeRunner(
            LxcNodeCommandResult(
                returncode=1,
                stderr="Profile not found",
            ),
            _profile_list("default"),
        )
        provider = _provider(runner, allow_live_mutation=False)

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("profile_missing", result.evidence["classification"])
        self.assertEqual("swarm-manager", result.evidence["node_name"])
        self.assertEqual("docker-swarm", result.evidence["expected_profile"])
        self.assertEqual("docker-swarm", result.evidence["resolved_profile"])
        self.assertEqual("default", result.evidence["available_profiles"])
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "profile", "list", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_provider_resource_resolution_blocks_when_lxd_network_missing(self):
        runner = _FakeRunner(
            _profile(),
            _name_list("default"),
            _name_list("default"),
        )
        provider = _provider(runner, config=_config(resolve_provider_resources=True))

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("network_missing", result.evidence["classification"])
        self.assertEqual("control", result.evidence["logical_network"])
        self.assertEqual("lxdbr0", result.evidence["resolved_network"])
        self.assertEqual("default", result.evidence["available_networks"])
        self.assertEqual("default", result.evidence["expected_storage_pool"])
        self.assertIn("resolved LXD network", result.evidence["remediation_hint"])
        self.assertEqual(
            [
                (("incus", "profile", "show", "docker-swarm"), 5.0),
                (("incus", "network", "list", "--format", "json"), 5.0),
            ],
            runner.calls[:2],
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_provider_resource_resolution_blocks_when_storage_pool_missing(self):
        runner = _FakeRunner(
            _profile(),
            _name_list("lxdbr0"),
            _name_list("other"),
        )
        provider = _provider(runner, config=_config(resolve_provider_resources=True))

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("storage_pool_missing", result.evidence["classification"])
        self.assertEqual("lxdbr0", result.evidence["available_networks"])
        self.assertEqual("default", result.evidence["expected_storage_pool"])
        self.assertEqual("other", result.evidence["available_storage_pools"])
        self.assertIn("expected LXD storage pool", result.evidence["remediation_hint"])
        self.assertEvidenceIsSummaryOnly(result)

    async def test_provider_resource_resolution_launches_with_resolved_network_and_storage(self):
        runner = _FakeRunner(
            _profile(),
            _name_list("lxdbr0"),
            _name_list("default"),
            _list(),
            _ok(),
            _list(_node("swarm-manager", "Running")),
        )
        provider = _provider(runner, config=_config(resolve_provider_resources=True))

        result = await provider.ensure_node(_node_spec(), _selection(ManagedLxcBackend.INCUS))

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        launch_call = runner.calls[4][0]
        self.assertEqual("launch", launch_call[1])
        self.assertIn("--network", launch_call)
        self.assertIn("lxdbr0", launch_call)
        self.assertIn("--storage", launch_call)
        self.assertIn("default", launch_call)
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
                (("incus", "delete", "swarm-manager", "--force"), 300.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_reset_managed_nodes_blocks_direct_project_proxy_devices(self):
        runner = _FakeTeardownRunner(
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    devices=_project_proxy_devices(),
                )
            ),
        )
        provider = _provider(runner)

        result = await provider.reset_nodes((_node_spec(),), _selection(ManagedLxcBackend.LXD))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("managed_nodes_reset_blocked", result.evidence["classification"])
        self.assertEqual("unsafe_instance_devices", result.evidence["first_failure_mismatch_reasons"])
        self.assertEqual(
            "explicit_lxc_proxy_drift_repair_required",
            result.evidence["first_failure_repair_action"],
        )
        self.assertEqual(
            "tsw-proxy-8080",
            result.evidence["first_failure_stale_project_proxy_devices"],
        )
        self.assertEqual(
            [(("lxc", "list", "swarm-manager", "--format", "json"), 5.0)],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_reset_managed_nodes_blocks_non_project_proxy_devices(self):
        runner = _FakeTeardownRunner(
            _list(
                _node(
                    "swarm-manager",
                    "Running",
                    devices={
                        "operator-proxy": {
                            "type": "proxy",
                            "listen": "tcp:0.0.0.0:8080",
                            "connect": "tcp:127.0.0.1:8080",
                        }
                    },
                )
            ),
        )
        provider = _provider(runner)

        result = await provider.reset_nodes((_node_spec(),), _selection(ManagedLxcBackend.LXD))

        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("managed_nodes_reset_blocked", result.evidence["classification"])
        self.assertEqual("unsafe_instance_devices", result.evidence["first_failure_mismatch_reasons"])
        self.assertNotIn("first_failure_repair_action", result.evidence)
        self.assertEqual(
            [(("lxc", "list", "swarm-manager", "--format", "json"), 5.0)],
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
        self.assertEqual("swarm-worker-1", result.evidence["first_failure_node"])
        self.assertEqual(
            "managed_marker_not_true",
            result.evidence["first_failure_mismatch_reasons"],
        )
        self.assertEqual(
            "different",
            result.evidence["first_failure_observed_managed_marker"],
        )
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
        self.assertEqual("swarm-manager", result.evidence["first_failure_node"])
        self.assertEqual(
            "managed_marker_not_true",
            result.evidence["first_failure_mismatch_reasons"],
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
                (("incus", "delete", "swarm-manager", "--force"), 300.0),
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
            ],
            runner.calls,
        )
        self.assertEvidenceIsSummaryOnly(result)

    async def test_reset_delete_uses_dedicated_teardown_timeout(self):
        runner = _FakeTeardownRunner(
            _list(_node("swarm-manager", "Running")),
            _ok(),
            _list(),
        )
        provider = _provider(runner, teardown_timeout_seconds=42.0)

        result = await provider.reset_nodes(
            (_node_spec(),),
            _selection(ManagedLxcBackend.INCUS),
        )

        self.assertEqual(VerificationStatus.VERIFIED, result.status)
        self.assertEqual(
            [
                (("incus", "list", "swarm-manager", "--format", "json"), 5.0),
                (("incus", "delete", "swarm-manager", "--force"), 42.0),
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
        with self.assertRaises(ValueError):
            LxcNodeProvider(
                config_repository=_FakeConfigRepository(_config()),
                runner=_FakeRunner(),
                teardown_timeout_seconds=0,
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
    teardown_timeout_seconds: float = 300.0,
) -> LxcNodeProvider:
    return LxcNodeProvider(
        config_repository=_FakeConfigRepository(config or _config()),
        runner=runner,
        allow_live_mutation=allow_live_mutation,
        teardown_timeout_seconds=teardown_timeout_seconds,
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
    additional_profiles: tuple[str, ...] = (),
    resolve_provider_resources: bool = False,
) -> NodeProviderConfig:
    profiles = [
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
    ]
    if "docker-swarm-manager" in additional_profiles:
        profiles.append(
            NodeProviderProfileRequirement(
                name="docker-swarm-manager",
                backend_support=(ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD),
                risk_labels=("manager_proxy_profile_requires_profile_reconciliation",),
                privileged_default=False,
                nesting_required=False,
                syscall_interception_required=False,
                cgroup_policy="provider_default",
                apparmor_policy="provider_default",
                seccomp_policy="provider_default",
                capability_additions=(),
                host_network=False,
                host_mounts=(),
                live_mutation_consent_required=True,
                blocks_mutation_when_missing=True,
            )
        )
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
                additional_profiles=(
                    additional_profiles if node.role is NodeRole.MANAGER else ()
                ),
            )
            for node in (nodes or (_node_spec(),))
        ),
        profiles=tuple(profiles),
        verification_metadata=ProviderVerificationMetadata(
            readiness_timeout_seconds=5,
            evidence_summary_only=True,
            store_raw_output=False,
            checks=(
                "backend_readiness",
                "profile_requirements",
                *(
                    ("provider_resource_resolution",)
                    if resolve_provider_resources
                    else ()
                ),
            ),
        ),
    )


def _ok() -> LxcNodeCommandResult:
    return LxcNodeCommandResult(returncode=0, stdout="ok")


def _profile(
    *,
    name: str = "docker-swarm",
    config: dict[str, str] | None = None,
    devices: dict[str, dict[str, str]] | None = None,
) -> LxcNodeCommandResult:
    import json

    profile_config = config
    if profile_config is None and name == "docker-swarm":
        profile_config = _docker_swarm_profile_config()
    if profile_config is None:
        profile_config = {}
    return LxcNodeCommandResult(
        returncode=0,
        stdout=json.dumps(
            {
                "name": name,
                "config": profile_config,
                "devices": devices or {},
            }
        ),
    )


def _profile_list(*names: str) -> LxcNodeCommandResult:
    return _name_list(*names)


def _name_list(*names: str) -> LxcNodeCommandResult:
    import json

    return LxcNodeCommandResult(
        returncode=0,
        stdout=json.dumps([{"name": name} for name in names]),
    )


def _docker_swarm_profile_config() -> dict[str, str]:
    return {
        "security.nesting": "true",
        "security.syscalls.intercept.mknod": "true",
        "security.syscalls.intercept.setxattr": "true",
    }


def _project_proxy_devices() -> dict[str, dict[str, str]]:
    return {
        "tsw-proxy-8080": {
            "type": "proxy",
            "listen": "tcp:0.0.0.0:8080",
            "connect": "tcp:127.0.0.1:8080",
        }
    }


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
        token in {"delete", "remove", "restart", "stop", "exec", "config"}
        for token in argv
    ):
        raise AssertionError(f"unsafe provider command was called: {argv!r}")
    if argv[:3] in {("incus", "profile", "list"), ("lxc", "profile", "list")}:
        if len(argv) != 5 or argv[3:] != ("--format", "json"):
            raise AssertionError(f"unexpected provider profile list was called: {argv!r}")
        return
    if argv[:3] in {("incus", "network", "list"), ("lxc", "network", "list")}:
        if len(argv) != 5 or argv[3:] != ("--format", "json"):
            raise AssertionError(f"unexpected provider network list was called: {argv!r}")
        return
    if argv[:3] in {("incus", "storage", "list"), ("lxc", "storage", "list")}:
        if len(argv) != 5 or argv[3:] != ("--format", "json"):
            raise AssertionError(f"unexpected provider storage list was called: {argv!r}")
        return
    if argv[:3] in {("incus", "profile", "create"), ("lxc", "profile", "create")}:
        if len(argv) != 4 or argv[3] not in {"docker-swarm", "docker-swarm-manager"}:
            raise AssertionError(f"unexpected provider profile create was called: {argv!r}")
        return
    if argv[:3] in {("incus", "profile", "set"), ("lxc", "profile", "set")}:
        allowed_settings = {
            "security.nesting": "true",
            "security.syscalls.intercept.mknod": "true",
            "security.syscalls.intercept.setxattr": "true",
        }
        if (
            len(argv) != 6
            or argv[3] != "docker-swarm"
            or allowed_settings.get(argv[4]) != argv[5]
        ):
            raise AssertionError(f"unexpected provider profile set was called: {argv!r}")
        return
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
