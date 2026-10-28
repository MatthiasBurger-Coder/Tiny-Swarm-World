"""Synthetic policy fixtures exercise admission, not real upgrade qualification."""
from pathlib import Path
import unittest

from pydantic import ValidationError

from tests.domain.lifecycle.test_models import manifest_fixture
from tiny_swarm_world.domain.lifecycle.models import (
    ComponentUpdateTarget, ComponentUpdateTransition, ServiceDefinition,
)
from tiny_swarm_world.domain.lifecycle.selection import plan_selection
from tiny_swarm_world.domain.lifecycle.update_planning import plan_component_updates
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

ROOT = Path(__file__).resolve().parents[3]


def update_fixture(requested=("jenkins", "nexus"), *, qualified=True):
    catalog = NativeComponentCatalog(ROOT).load()
    selection = plan_selection(catalog, requested)
    definitions = []
    components = []
    for service in catalog.services:
        bundle = service.components
        if qualified and service.service_id in requested and service.kind == "stack":
            bundle = tuple(item.model_copy(update={"desired": item.desired.model_copy(update={"image_digest": "sha256:" + "a" * 64})})
                           for item in bundle)
            sources = {item.component_id: item.desired for item in bundle}
            versions = {name: version.model_copy(update={"image_tag": "test-next", "image_digest": "sha256:" + "b" * 64})
                        for name, version in sources.items()}
            target = ComponentUpdateTarget(target_id="test-next", versions=versions, qualification="qualified-transition",
                                           metadata_source="synthetic-test-policy")
            transition = ComponentUpdateTransition(
                target_id=target.target_id, source_versions=sources, migrations=("test-schema",), backup_required=True,
                availability_impact="Selected service restarts; dependent requests may be unavailable.",
                recovery_limit="Verified compatible backup required; image rollback is not data restore.",
            )
            service = service.model_copy(update={"components": bundle, "update_targets": (target,),
                                                 "update_transitions": (transition,), "migration_policy": "explicit-transitions"})
        definitions.append(service)
        if service.service_id in selection.resolved_services:
            components.extend(item.model_copy(update={"observed": item.desired}) for item in bundle)
    catalog = catalog.model_copy(update={"services": tuple(definitions)})
    manifest = manifest_fixture().model_copy(update={
        "requested_services": selection.requested_services, "resolved_services": selection.resolved_services,
        "selection_reasons": selection.selection_reasons, "service_preset": selection.service_preset,
        "components": tuple(components),
    })
    return catalog, manifest


class UpdatePlanningTests(unittest.TestCase):
    def test_batch_order_exact_images_migrations_and_no_implicit_updates(self):
        catalog, manifest = update_fixture()
        first = plan_component_updates(catalog, manifest, ("jenkins", "nexus"))
        second = plan_component_updates(catalog, manifest, ("nexus", "jenkins"))
        self.assertEqual(first, second)
        self.assertEqual(first.dependency_order, ("nexus", "jenkins"))
        self.assertEqual(first.status, "preview")
        self.assertEqual({item.service_id for item in first.services}, {"nexus", "jenkins"})
        for service in first.services:
            self.assertEqual(service.status, "planned")
            self.assertTrue(service.backup_required)
            self.assertEqual(service.migrations, ("test-schema",))
            self.assertIn("restarts", service.availability_impact)
            self.assertIn("backup", service.recovery_limit)
            self.assertTrue(all(item.target.image_digest and item.desired_change for item in service.components))
        self.assertIn("portainer", first.services[0].dependencies)
        self.assertIn("jenkins", first.services[0].affected_dependents)

    def test_single_bundle_and_explicit_target(self):
        catalog, manifest = update_fixture(("swagger",))
        plan = plan_component_updates(catalog, manifest, ("swagger",), "test-next")
        self.assertEqual(plan.status, "preview")
        self.assertEqual(len(plan.services[0].components), 4)
        self.assertTrue(all(item.target.image_digest for item in plan.services[0].components))

    def test_verified_recorded_noop_is_repeatable_without_live_claim(self):
        catalog, manifest = update_fixture(("nexus",))
        target = next(item for item in catalog.services if item.service_id == "nexus").update_targets[0]
        components = tuple(item.model_copy(update={"desired": target.versions[item.component_id], "observed": target.versions[item.component_id]})
                           if item.service_id == "nexus" else item for item in manifest.components)
        manifest = manifest.model_copy(update={"components": components})
        plan = plan_component_updates(catalog, manifest, ("nexus",))
        self.assertEqual(plan.status, "no_op")
        self.assertEqual(plan, plan_component_updates(catalog, manifest, ("nexus",)))
        self.assertEqual(plan.observation_source, "recorded-manifest-not-live")
        self.assertFalse(plan.services[0].components[0].desired_change)
        missing = manifest.model_copy(update={"components": tuple(item.model_copy(update={"observed": None}) for item in components)})
        self.assertEqual(plan_component_updates(catalog, missing, ("nexus",)).status, "blocked")

    def test_observation_missing_and_drift_block_admitted_transition(self):
        catalog, manifest = update_fixture(("nexus",))
        for observed in (None, manifest.components[-1].desired.model_copy(update={"image_digest": "sha256:" + "c" * 64})):
            components = tuple(item.model_copy(update={"observed": observed}) if item.service_id == "nexus" else item
                               for item in manifest.components)
            result = plan_component_updates(catalog, manifest.model_copy(update={"components": components}), ("nexus",))
            self.assertEqual(result.services[0].status, "blocked")
            self.assertTrue(result.services[0].components[0].drift)

    def test_extra_desired_metadata_drift_cannot_hide_behind_matching_digest(self):
        catalog, manifest = update_fixture(("nexus",))
        service = next(item for item in catalog.services if item.service_id == "nexus")
        for at_target, observed_version in ((False, None), (True, None), (False, "different-version"), (True, "different-version")):
            components = []
            for item in manifest.components:
                if item.service_id == "nexus":
                    identity = service.update_targets[0].versions[item.component_id] if at_target else item.desired
                    desired = identity.model_copy(update={"upstream_version": "declared-version"})
                    observed = identity.model_copy(update={"upstream_version": observed_version})
                    item = item.model_copy(update={"desired": desired, "observed": observed})
                components.append(item)
            plan = plan_component_updates(catalog, manifest.model_copy(update={"components": tuple(components)}), ("nexus",))
            self.assertEqual(plan.status, "blocked")
            self.assertNotIn(plan.services[0].status, {"planned", "no_op"})
            self.assertIn("upstream_version_unknown" if observed_version is None else "upstream_version_mismatch",
                          plan.services[0].components[0].drift)

    def test_native_baseline_is_not_an_upgrade_or_verified_noop(self):
        catalog, manifest = update_fixture(("nexus",), qualified=False)
        for target in (None, "native-baseline", "latest", "unknown"):
            plan = plan_component_updates(catalog, manifest, ("nexus",), target)
            self.assertEqual(plan.status, "blocked")
            self.assertEqual(plan.services[0].status, "unsupported")
        self.assertFalse(any(item.update_transitions for item in catalog.services if item.service_id not in {"portainer", "swagger", "traefik"}))

    def test_invalid_unknown_duplicate_empty_and_uninstalled_selection(self):
        catalog, manifest = update_fixture(("nexus",))
        for requested in ((), ("nexus", "nexus"), ("unknown",), ("*",), ("jenkins",)):
            with self.subTest(requested=requested), self.assertRaises(ValueError):
                plan_component_updates(catalog, manifest, requested)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            plan_component_updates(catalog, manifest, ("nexus", "portainer"), "test-next")

    def test_downgrade_host_and_preset_compatibility_fail(self):
        catalog, manifest = update_fixture(("nexus",))
        service = next(item for item in catalog.services if item.service_id == "nexus")
        for target in (service.update_targets[0].model_copy(update={"hosts": ("wsl2",)}),
                       service.update_targets[0].model_copy(update={"presets": ("default",)})):
            changed = catalog.model_copy(update={"services": tuple(item.model_copy(update={"update_targets": (target,)})
                                                                  if item == service else item for item in catalog.services)})
            self.assertEqual(plan_component_updates(changed, manifest, ("nexus",)).status, "blocked")
        newer = tuple(item.model_copy(update={"desired": item.desired.model_copy(update={"image_tag": "newer"})})
                      if item.service_id == "nexus" else item for item in manifest.components)
        self.assertEqual(plan_component_updates(catalog, manifest.model_copy(update={"components": newer}), ("nexus",)).services[0].status, "unsupported")

    def test_portainer_dedicated_and_incus_host_owner(self):
        catalog, manifest = update_fixture(("nexus",))
        plan = plan_component_updates(catalog, manifest, ("portainer", "incus"))
        self.assertEqual(plan.dependency_order, ("incus", "portainer"))
        self.assertEqual(plan.services[0].status, "unsupported")
        self.assertIn("host operator", plan.services[0].reason)
        self.assertEqual(plan.services[1].status, "dedicated_upgrade")
        self.assertEqual(plan.services[1].lifecycle_owner, "portainer-adapter")

    def test_policy_requires_complete_pinned_bundle_and_backup(self):
        catalog, _ = update_fixture(("nexus",))
        service = next(item for item in catalog.services if item.service_id == "nexus")
        payload = service.model_dump()
        for change in (
            {"update_targets": (service.update_targets[0].model_copy(update={"versions": {}}),)},
            {"update_targets": (service.update_targets[0].model_copy(update={"versions": {name: item.model_copy(update={"image_digest": None}) for name, item in service.update_targets[0].versions.items()}}),)},
            {"update_transitions": (service.update_transitions[0].model_copy(update={"backup_required": False}),)},
            {"update_transitions": (service.update_transitions[0].model_copy(update={"target_id": "unknown"}),)},
        ):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                ServiceDefinition.model_validate(dict(payload, **change))
