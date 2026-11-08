"""Desired management modes never infer verified Portainer object identities."""
import unittest
from pathlib import Path
from tests.domain.lifecycle.test_models import manifest_fixture
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.domain.lifecycle.selection import SelectionError, plan_selection


def catalog():
    return NativeComponentCatalog(Path(__file__).resolve().parents[3]).load()


def manifest():
    plan = plan_selection(catalog(), ('swagger',))
    return manifest_fixture().model_copy(update={
        'requested_services': plan.requested_services, 'resolved_services': plan.resolved_services,
        'selection_reasons': plan.selection_reasons})


class StackManagementSelectionTests(unittest.TestCase):
    def test_fresh_explicit_portainer_mode_is_separate_from_verified_ids(self):
        plan = plan_selection(catalog(), ('jenkins',), stack_owner='portainer')
        self.assertTrue(plan.stack_owners)
        self.assertEqual(set(plan.stack_owners.values()), {'portainer'})
        self.assertNotIn('stack_id', plan.model_dump_json())
    def test_default_and_v1_remain_swarm(self):
        plan = plan_selection(catalog(), ('jenkins',))
        self.assertEqual(set(plan.stack_owners.values()), {'swarm'})
    def test_existing_owner_cannot_be_rewritten_by_flag(self):
        with self.assertRaises(SelectionError):
            plan_selection(catalog(), ('jenkins',), persisted=manifest(), stack_owner='portainer')
    def test_add_retains_existing_swarm_mode(self):
        current = manifest()
        plan = plan_selection(catalog(), ('jenkins',), persisted=current, add=True, stack_owner='portainer')
        for name in current.effective_stack_ownership():
            self.assertEqual(plan.stack_owners[name], 'swarm')
