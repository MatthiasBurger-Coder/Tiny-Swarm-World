"""Network relation ordering is stable without concealing inventory drift."""
from __future__ import annotations

import copy
import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests.test_network_preparation import MockHost, PACKAGE, ROOT
from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.adapters.network_preparation.adapter import LocalNetworkPreparation
from tiny_swarm_world.infrastructure.adapters.network_preparation import inventory


class NetworkResourceProjectionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.host = MockHost(Path(self.directory.name))
        self.adapter = LocalNetworkPreparation(
            ROOT, ROOT / "infra/config", release="24.04", profile="service-access",
            proc_root=self.host.proc, target_snapshot=lambda: (self.host.source,), evidence=Mock())

    async def observe(self):
        with self.host.patches():
            return await inventory.inspect_network(self.adapter)

    async def test_every_relation_permutation_has_identical_snapshot(self):
        relations = ["/1.0/instances/worker?project=default", "/1.0/profiles/default", "/1.0/instances/manager"]
        snapshots = []
        for permutation in itertools.permutations(relations):
            self.host.networks[0]["used_by"] = list(permutation)
            snapshots.append(await self.observe())
        self.assertTrue(all(value == snapshots[0] for value in snapshots))
        self.assertFalse(snapshots[0].blockers)

    async def test_membership_duplicates_and_uri_bytes_remain_observable(self):
        self.host.networks[0]["used_by"] = ["/1.0/profiles/default", "/1.0/instances/a?project=default"]
        baseline = await self.observe()
        variants = [
            ["/1.0/profiles/default"],
            ["/1.0/profiles/default", "/1.0/instances/a?project=default", "/1.0/instances/b"],
            ["/1.0/profiles/default", "/1.0/instances/a?project=other"],
            ["/1.0/profiles/default", "/1.0/instances/a?project=default", "/1.0/profiles/default"],
            ["/1.0/profiles/default", "/1.0/instances/%61?project=default"],
        ]
        for relations in variants:
            with self.subTest(relations=relations):
                self.host.networks[0]["used_by"] = relations
                current = await self.observe()
                self.assertNotEqual(current.fingerprint, baseline.fingerprint)
                self.assertNotEqual(current.invariant, baseline.invariant)

    async def test_missing_relation_field_stays_distinct_from_empty_list(self):
        baseline = await self.observe()
        self.host.networks[0]["used_by"] = []
        current = await self.observe()
        self.assertNotEqual(current.invariant, baseline.invariant)

    async def test_malformed_present_relations_fail_explicitly(self):
        for value in (None, "", "/1.0/profiles/default", {}, (), 1, [None], [1], [True], [["uri"]]):
            with self.subTest(value=value):
                self.host.networks[0]["used_by"] = value
                with self.assertRaises(NetworkPreparationFailure):
                    await self.observe()

    async def test_projection_preserves_raw_inventory_and_bridge_resolution_input(self):
        raw = self.host.networks
        raw[0]["used_by"] = ["z", "a", "a"]
        before = copy.deepcopy(raw)
        original = inventory.incus.named_resources

        def resources(value, kind):
            return raw if kind == "networks" else original(value, kind)

        with self.host.patches(), patch.object(inventory.incus, "named_resources", side_effect=resources), \
                patch(PACKAGE + ".configuration.resolve_bridges", wraps=inventory.configuration.resolve_bridges) as bridges:
            await inventory.inspect_network(self.adapter)
        self.assertIs(bridges.call_args.args[1], raw)
        self.assertEqual(raw, before)

    async def test_unrelated_nested_order_remains_fingerprint_sensitive(self):
        self.host.networks[0]["observation"] = {"used_by": ["z", "a"], "ordered": [1, 2]}
        baseline = await self.observe()
        self.host.networks[0]["observation"]["used_by"].reverse()
        current = await self.observe()
        self.assertNotEqual(current.invariant, baseline.invariant)
        self.host.networks[0]["observation"]["ordered"].reverse()
        self.assertNotEqual((await self.observe()).invariant, current.invariant)

    async def test_outer_resource_order_remains_fingerprint_sensitive(self):
        self.host.networks.append(dict(self.host.networks[0], name="foreign-observation", managed=False,
                                       config={"ipv4.address": "none"}))
        baseline = await self.observe()
        self.host.networks.reverse()
        self.assertNotEqual((await self.observe()).invariant, baseline.invariant)
