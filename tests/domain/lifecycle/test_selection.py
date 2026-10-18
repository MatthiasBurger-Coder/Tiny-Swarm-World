from pathlib import Path
import unittest

from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog
from tiny_swarm_world.domain.lifecycle.selection import SelectionError, plan_selection
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

ROOT = Path(__file__).resolve().parents[3]


class SelectionPlanningTests(unittest.TestCase):
    def setUp(self):
        self.catalog = NativeComponentCatalog(ROOT).load()

    def test_transitive_closure_deterministic_and_explained(self):
        first = plan_selection(self.catalog, ("jenkins", "swagger"))
        second = plan_selection(self.catalog, ("swagger", "jenkins"))
        self.assertEqual(first, second)
        self.assertEqual(first.resolved_services, ("incus", "portainer", "nexus", "jenkins", "swagger"))
        self.assertEqual(first.selection_reasons["nexus"], ("jenkins",))
        self.assertTrue(first.resources.unknowns)
        self.assertTrue(all(total is None for total in first.resources.totals.values()))

    def test_minimal_has_foundations_and_no_preset_expansion(self):
        result = plan_selection(self.catalog, minimal=True)
        self.assertEqual(result.requested_services, ())
        self.assertEqual(result.resolved_services, ("incus", "portainer"))
        self.assertEqual(set(result.selection_reasons), {"incus", "portainer"})

    def test_cli_over_configuration_and_preset_conflicts(self):
        result = plan_selection(self.catalog, ("jenkins",), ("pulsar",))
        self.assertEqual(result.requested_services, ("jenkins",))
        configured = plan_selection(self.catalog, configured=("pulsar",))
        self.assertEqual(configured.source, "configuration")
        for kwargs in ({"minimal": True, "preset": "default"},
                       {"requested": ("jenkins",), "preset": "default"},
                       {"preset": "unknown"}, {"minimal": True, "configured": ("pulsar",)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(SelectionError):
                plan_selection(self.catalog, **kwargs)

    def test_strict_ids_foundations_and_capabilities(self):
        for names in ((), ("",), ("Jenkins",), ("*",), ("unknown",), ("jenkins", "jenkins")):
            with self.subTest(names=names), self.assertRaises(SelectionError):
                plan_selection(self.catalog, names)
        for name in ("incus", "portainer"):
            with self.subTest(name=name), self.assertRaisesRegex(SelectionError, "foundations"):
                plan_selection(self.catalog, remove=(name,))
        with self.assertRaisesRegex(SelectionError, "capabilities"):
            plan_selection(self.catalog, minimal=True, available_capabilities=())
        self.assertEqual(plan_selection(self.catalog, minimal=True, available_capabilities=(
            "managed-lxc", "docker-swarm", "shared-overlay")).resolved_services, ("incus", "portainer"))

    def test_bad_catalog_graph_is_rejected_before_planning(self):
        for dependency in ("unknown", "jenkins"):
            services = tuple(item.model_copy(update={"dependencies": (dependency,)})
                             if item.service_id == "nexus" else item for item in self.catalog.services)
            with self.subTest(dependency=dependency), self.assertRaises(SelectionError):
                plan_selection(ComponentCatalog(services=services), minimal=True)
        with self.assertRaisesRegex(SelectionError, "duplicate"):
            plan_selection(ComponentCatalog(services=self.catalog.services + self.catalog.services[:1]))

    def test_presets_and_resource_totals(self):
        default = plan_selection(self.catalog, preset="default")
        extended = plan_selection(self.catalog, preset="service-access")
        self.assertNotIn("infisical", default.resolved_services)
        self.assertIn("infisical", extended.resolved_services)
        services = tuple(item.model_copy(update={"resources": item.resources.model_copy(update={
            "declared": {item.service_id: {"limits": {"cpus": "1.5", "memory": "1GiB"},
                                            "reservations": {"cpus": "0.5", "memory": "512MiB"}}}})})
                         for item in self.catalog.services)
        result = plan_selection(ComponentCatalog(services=services), minimal=True)
        self.assertEqual(result.resources.totals["limits_cpus"], "3.0")
        self.assertEqual(result.resources.totals["limits_memory"], 2 * 1024 ** 3)
        self.assertEqual(result.resources.unknowns, ())
