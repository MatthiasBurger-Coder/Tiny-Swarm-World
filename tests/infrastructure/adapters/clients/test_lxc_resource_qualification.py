"""Qualification contract tests without constructing a lifecycle provider."""

import unittest
from dataclasses import replace
from unittest.mock import AsyncMock, Mock

from tests.infrastructure.adapters.clients.test_lxc_node_provider import (
    _config,
    _FakeRunner,
    _name_list,
    _node_spec,
    _provider,
    _ResourceInspector,
    _selection,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import (
    LxcNodeCommandResult,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.qualification import (
    LxcResourceQualification,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.resolution import (
    resources_supported,
)


class TestLxcResourceQualification(unittest.IsolatedAsyncioTestCase):
    def test_supported_and_unsupported_limits(self):
        for limits in ({}, {"cpu": "2", "memory": "4GiB", "disk": "20G"}):
            with self.subTest(limits=limits):
                self.assertTrue(resources_supported(limits))
        for limits in (
            {"raw": "true"},
            {"cpu": "0"},
            {"cpu": "two"},
            {"memory": "unlimited"},
            {"disk": "-1GiB"},
        ):
            with self.subTest(limits=limits):
                self.assertFalse(resources_supported(limits))

    def test_capacity_fits_and_rejects_aggregate_plan_without_commands(self):
        runner = _FakeRunner()
        qualification = LxcResourceQualification(runner)
        config = _config(resources={"cpu": "2", "memory": "2GiB"})
        node = _node_spec()
        selection = _selection(ManagedLxcBackend.INCUS)
        self.assertIsNone(
            qualification.host_capacity_block(
                node,
                selection,
                config,
                _ResourceInspector(),
            )
        )
        config = replace(
            config,
            nodes=(
                config.nodes[0],
                replace(
                    config.nodes[0],
                    spec=_node_spec(name="swarm-worker"),
                ),
            ),
        )
        result = qualification.host_capacity_block(
            node, selection, config, _ResourceInspector()
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(VerificationStatus.BLOCKED, result.status)
        self.assertEqual("host_capacity_exceeded", result.evidence["classification"])
        self.assertEqual("4", result.evidence["planned_cpu_threads"])
        self.assertEqual(str(4 * 1024**3), result.evidence["planned_memory_bytes"])
        self.assertEqual("not_started", result.evidence["mutation"])
        self.assertNotIn("backend", result.evidence)
        self.assertEqual([], runner.calls)

    def test_optional_or_untyped_inspector_preserves_capacity_noop(self):
        qualification = LxcResourceQualification(_FakeRunner())
        for inspector in (None, object(), Mock(inspect=Mock(return_value=object()))):
            with self.subTest(inspector=inspector):
                self.assertIsNone(
                    qualification.host_capacity_block(
                        _node_spec(),
                        _selection(ManagedLxcBackend.INCUS),
                        _config(),
                        inspector,
                    )
                )

    async def test_resolution_disabled_does_not_probe(self):
        runner = _FakeRunner()
        config = _config()
        result = await LxcResourceQualification(runner).verify_provider_resources(
            _node_spec(),
            _selection(ManagedLxcBackend.INCUS),
            ManagedLxcBackend.INCUS,
            config,
            config.nodes[0],
        )
        self.assertIsNone(result)
        self.assertEqual([], runner.calls)

    async def test_supported_backends_probe_network_then_storage_only(self):
        for backend, executable, network in (
            (ManagedLxcBackend.INCUS, "incus", "incusbr0"),
            (ManagedLxcBackend.LXD, "lxc", "lxdbr0"),
        ):
            with self.subTest(backend=backend):
                runner = _FakeRunner(_name_list(network), _name_list("default"))
                config = _config(resolve_provider_resources=True)
                result = await LxcResourceQualification(
                    runner
                ).verify_provider_resources(
                    _node_spec(),
                    _selection(backend),
                    backend,
                    config,
                    config.nodes[0],
                )
                self.assertIsNone(result)
                self.assertEqual(
                    [
                        ((executable, "network", "list", "--format", "json"), 5.0),
                        ((executable, "storage", "list", "--format", "json"), 5.0),
                    ],
                    runner.calls,
                )

    async def test_incomplete_mapping_blocks_without_probes(self):
        config = _config(resolve_provider_resources=True)
        for candidate, node_config in (
            (replace(config, provider_resource_resolution=None), config.nodes[0]),
            (config, replace(config.nodes[0], networks=())),
            (config, replace(config.nodes[0], networks=("unknown",))),
        ):
            with self.subTest(node_config=node_config, candidate=candidate):
                runner = _FakeRunner()
                result = await LxcResourceQualification(
                    runner
                ).verify_provider_resources(
                    _node_spec(),
                    _selection(ManagedLxcBackend.INCUS),
                    ManagedLxcBackend.INCUS,
                    candidate,
                    node_config,
                )
                assert result is not None
                self.assertEqual(
                    "inventory_mapping_missing", result.evidence["classification"]
                )
                self.assertEqual([], runner.calls)

    async def test_failed_and_malformed_probes_block_and_keep_diagnostics_private(self):
        failures = (
            LxcNodeCommandResult(1, "secret-token /home/operator", "permission denied"),
            LxcNodeCommandResult(0, "secret-token", ""),
            LxcNodeCommandResult(0, '{"name":"incusbr0"}', ""),
            LxcNodeCommandResult(0, '[null, 7, {"name": 3}]', ""),
            LxcNodeCommandResult(
                0, '[{"name":"incusbr0"}]', "secret-token", timed_out=True
            ),
        )
        config = _config(resolve_provider_resources=True)
        for probe in ("network", "storage"):
            for failure in failures:
                with self.subTest(probe=probe, failure=failure):
                    runner = _FakeRunner(
                        *(
                            (failure,)
                            if probe == "network"
                            else (_name_list("incusbr0"), failure)
                        )
                    )
                    result = await LxcResourceQualification(
                        runner
                    ).verify_provider_resources(
                        _node_spec(),
                        _selection(ManagedLxcBackend.INCUS),
                        ManagedLxcBackend.INCUS,
                        config,
                        config.nodes[0],
                    )
                    assert result is not None
                    self.assertEqual(VerificationStatus.BLOCKED, result.status)
                    self.assertEqual("pre_apply", result.evidence["phase"])
                    self.assertEqual(
                        "network_missing"
                        if probe == "network"
                        else "storage_pool_missing",
                        result.evidence["classification"],
                    )
                    self.assertEqual(1 if probe == "network" else 2, len(runner.calls))
                    for forbidden in (
                        "secret-token",
                        "/home/operator",
                        "permission denied",
                        "stdout",
                        "stderr",
                    ):
                        self.assertNotIn(forbidden, repr(result.to_dict()))

    async def test_provider_delegates_and_propagates_same_block_result(self):
        node = _node_spec()
        selection = _selection(ManagedLxcBackend.INCUS)
        config = _config(resolve_provider_resources=True)
        blocked = VerificationResult(
            "platform:node:swarm-manager",
            VerificationStatus.BLOCKED,
            "qualification blocked",
            {"classification": "network_missing"},
        )
        runner = _FakeRunner()
        provider = _provider(runner, config=config)
        with unittest.mock.patch.object(
            provider.resource_qualification, "host_capacity_block", return_value=None
        ) as capacity:
            with unittest.mock.patch.object(
                provider.resource_qualification,
                "verify_provider_resources",
                new=AsyncMock(return_value=blocked),
            ) as resources:
                self.assertIs(blocked, await provider.ensure_node(node, selection))
                capacity.assert_called_once_with(node, selection, config, None)
                resources.assert_awaited_once_with(
                    node, selection, ManagedLxcBackend.INCUS, config, config.nodes[0]
                )
        self.assertEqual([], runner.calls)
