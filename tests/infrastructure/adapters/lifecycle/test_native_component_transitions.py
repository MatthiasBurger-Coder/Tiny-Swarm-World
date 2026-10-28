"""Real native policy through Classic update, persistence and recovery; runtime is mocked."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

from tests.domain.lifecycle.test_models import manifest_fixture
from tiny_swarm_world.application.services.component_execution import ComponentUpdateExecution
from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.deployment.workflows import DeploymentWorkflowStatus
from tiny_swarm_world.application.services.platform.workflow.update import ClassicUpdateWorkflow
from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.domain.deployment import ComposeServiceDefinition
from tiny_swarm_world.domain.lifecycle.selection import plan_selection
from tiny_swarm_world.domain.lifecycle.update_planning import plan_component_updates
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import UpdateRuntimeObservation, UpdateTaskObservation
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.component_runtime import ClassicComponentRuntime, image_reference
from tiny_swarm_world.infrastructure.adapters.lifecycle.desired_images import effective_image_environment, effective_component_inventory
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml, resolve_container_image_contracts,
)
from tiny_swarm_world.infrastructure.adapters.update.json_state_store import JsonUpdateStateStore
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths

ROOT = Path(__file__).resolve().parents[4]
CONSENT = LiveConsent(True, confirmed=True)


def native_installation(*, promote_candidates=True):
    catalog = NativeComponentCatalog(ROOT).load()
    if promote_candidates:
        catalog = catalog.model_copy(update={"services": tuple(
            service.model_copy(update={"update_targets": tuple(
                target.model_copy(update={"qualification": "qualified-transition"})
                if target.qualification == "candidate-transition" else target
                for target in service.update_targets
            )}) for service in catalog.services
        )})
    selection = plan_selection(catalog, ("swagger", "traefik"))
    components = []
    for service in catalog.services:
        if service.service_id not in selection.resolved_services:
            continue
        sources = service.update_transitions[0].source_versions if service.service_id in {"swagger", "traefik"} else {}
        for component in service.components:
            desired = sources.get(component.component_id, component.desired)
            components.append(component.model_copy(update={"desired": desired, "observed": desired}))
    manifest = manifest_fixture().model_copy(update={
        "requested_services": selection.requested_services, "resolved_services": selection.resolved_services,
        "selection_reasons": selection.selection_reasons, "service_preset": selection.service_preset,
        "components": tuple(components),
    })
    return catalog, manifest


class NativeTransitionPlanningTests(unittest.TestCase):
    def test_unqualified_catalog_candidates_cannot_be_planned(self):
        catalog, manifest = native_installation(promote_candidates=False)
        service = next(item for item in catalog.services if item.service_id == "traefik")
        target = next(item for item in service.update_targets if item.target_id == "traefik-3-7-5")
        self.assertEqual(target.qualification, "candidate-transition")
        for target_id in (None, "traefik-3-7-5"):
            with self.subTest(target_id=target_id):
                result = plan_component_updates(catalog, manifest, ("traefik",), target_id)
                self.assertEqual(result.status, "blocked")
                self.assertEqual(result.services[0].status, "unsupported")

    def test_catalog_pins_are_exact_child_manifests_not_indexes(self):
        catalog, manifest = native_installation()
        service = next(s for s in catalog.services if s.service_id == "traefik")
        transition = service.update_transitions[0]
        self.assertEqual(transition.source_versions["traefik"].image_digest,
                         "sha256:580f70e21a5b63503dcbd5690b432b0e78b056e931a1738a5ca2d997bd08bc47")
        target = next(t for t in service.update_targets if t.target_id == transition.target_id)
        self.assertEqual(target.versions["traefik"].image_digest,
                         "sha256:e5491c6c7073c18a2fa8ae48196630d64894b41d877aca1babe4a3ad98bd5cba")
        for definition in catalog.services:
            for policy in definition.update_transitions:
                for identity in policy.source_versions.values():
                    self.assertRegex(identity.image_digest, r"^sha256:[0-9a-f]{64}$")
        components = tuple(c.model_copy(update={"observed": c.desired.model_copy(update={
            "image_digest": "sha256:fcdef599e6259359833dd2e1d49f9e964f66825d69bd3dd468f51102ce013d03"})})
                           if c.component_id == "traefik" else c for c in manifest.components)
        self.assertEqual(plan_component_updates(catalog, manifest.model_copy(update={"components": components}), ("traefik",)).status, "blocked")

    def test_exact_native_bundle_and_only_changed_images_for_both_hosts(self):
        catalog, manifest = native_installation()
        for host in ("native-linux", "wsl2"):
            plan = plan_component_updates(catalog, manifest.model_copy(update={"host": host}), ("traefik", "swagger"))
            self.assertEqual(plan.status, "preview")
            self.assertEqual(plan.dependency_order, ("swagger", "traefik"))
            changes = {c.component_id for s in plan.services for c in s.components if c.desired_change}
            self.assertEqual(changes, {"swagger-ui", "traefik"})
            self.assertEqual(sum(len(s.components) for s in plan.services), 5)
            self.assertFalse(any(s.backup_required or s.migrations for s in plan.services))
            self.assertTrue(all(c.target.image_digest for s in plan.services for c in s.components))

    def test_native_digest_drift_unknown_source_and_retained_sibling_drift_block(self):
        catalog, manifest = native_installation()
        for name, field in (("swagger-ui", "desired"), ("swagger-ui", "observed"), ("swagger-api", "observed")):
            components = tuple(c.model_copy(update={field: c.desired.model_copy(update={"image_digest": "sha256:" + "f" * 64})})
                               if c.component_id == name else c for c in manifest.components)
            changed = manifest.model_copy(update={"components": components})
            self.assertEqual(plan_component_updates(catalog, changed, ("swagger",)).status, "blocked")
        baseline = tuple(c.model_copy(update={"desired": c.desired.model_copy(update={"image_digest": None})})
                         if c.component_id == "swagger-ui" else c for c in manifest.components)
        self.assertEqual(plan_component_updates(catalog, manifest.model_copy(update={"components": baseline}), ("swagger",)).status, "blocked")


class NativeTransitionExecutionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        catalog, self.original = native_installation()
        self.catalog = Mock(load=Mock(return_value=catalog))
        self.manifests = JsonManifestRepository(self.root / ".tiny-swarm-world/installation/manifest.json")
        self.manifests.save(self.original, expected_token=None)
        self.images = {c.component_id: image_reference(c.desired) for c in self.original.components
                       if c.service_id in {"swagger", "traefik"}}
        self.calls = []
        self.fail = set()
        self.old_tasks = set()
        self.observer = Mock(observe=AsyncMock(side_effect=self.observe))
        compose = Mock(get_services_of=Mock(side_effect=lambda stack: tuple(
            ComposeServiceDefinition(name=c.component_id, image_ref=self.images[c.component_id])
            for c in self.original.components if c.service_id == stack)))
        self.store = JsonUpdateStateStore(self.root / "classic-updates")
        workflow = ClassicUpdateWorkflow(compose, self.deployment, self.store, self.observer,
                                         verification_attempts=2, poll_interval_seconds=0)
        self.journal = JsonUpdateJournal(self.manifests.path.parent / "component-update.json")
        self.executor = ComponentUpdateExecution(ComponentUpdateService(self.manifests, self.catalog),
                                                 self.manifests, self.journal, ClassicComponentRuntime(workflow))

    async def observe(self, stack, name):
        image = self.images[name]
        old = next(c.desired for c in self.original.components if c.component_id == name)
        task = image_reference(old) if name in self.old_tasks else image
        return UpdateRuntimeObservation(stack, name, "id-" + name, 1, image, 1,
                                        (UpdateTaskObservation("task-" + name, task, "running", "running"),), "completed")

    def deployment(self, plan):
        async def run():
            self.calls.append(plan)
            status = DeploymentWorkflowStatus.FAILED_TO_APPLY if plan.service_name in self.fail else DeploymentWorkflowStatus.COMPLETED
            if status == DeploymentWorkflowStatus.COMPLETED:
                self.images[plan.service_name] = plan.target_image
            return SimpleNamespace(status=status, verification_results=())
        return SimpleNamespace(run=run)

    async def apply(self, services=("swagger", "traefik"), *, recovery=False):
        return await self.executor.run(services, consent=CONSENT, recovery=recovery)

    async def test_batch_persistence_real_compose_artifacts_noop_and_original_recovery(self):
        self.assertEqual((await self.apply())["status"], "completed")
        self.assertEqual([p.service_name for p in self.calls], ["swagger-ui", "traefik"])
        current = self.manifests.load().manifest
        self.assertEqual(current.credential_references, self.original.credential_references)
        self.assertEqual(current.installation_id, self.original.installation_id)
        retained = tuple(c for c in current.components if c.service_id not in {"swagger", "traefik"})
        self.assertEqual(retained, tuple(c for c in self.original.components if c.service_id not in {"swagger", "traefik"}))
        environment = effective_image_environment({}, self.root)
        contracts = resolve_container_image_contracts(tuple(c for c in DEFAULT_CONTAINER_IMAGE_CONTRACTS
                                                           if c.build_context in self.images), environment)
        self.assertEqual({c.build_context: c.image_ref for c in contracts}, self.images)
        paths = ProjectPaths.from_roots(self.root, ROOT / "infra")
        repository = ComposeFileRepositoryYaml(project_paths=paths, environment={}, write_logs=False)
        for stack in ("swagger", "traefik"):
            self.assertEqual({s.name: s.image_ref for s in repository.get_services_of(stack)},
                             {c.component_id: self.images[c.component_id] for c in current.components if c.service_id == stack})
        inventory = effective_component_inventory(self.catalog, current.resolved_services, current, self.root)
        self.assertEqual({c.component_id: c.desired for c in inventory}, {c.component_id: c.desired for c in current.components})
        journal = self.journal.load()
        self.assertEqual((await self.apply())["status"], "completed")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.journal.load().original, journal.original)
        self.assertEqual((await self.apply(recovery=True))["status"], "recovered")
        self.assertEqual([p.service_name for p in self.calls], ["swagger-ui", "traefik", "traefik", "swagger-ui"])
        self.assertEqual(tuple(c.desired for c in self.manifests.load().manifest.components),
                         tuple(c.desired for c in self.original.components))
        self.assertEqual((await self.apply(recovery=True))["status"], "recovered")
        self.assertEqual(len(self.calls), 4)

    async def test_partial_batch_failure_and_resume_keep_original_intent(self):
        self.fail.add("traefik")
        self.assertEqual((await self.apply())["status"], "partial")
        original = self.journal.load().original
        self.fail.clear()
        self.assertEqual((await self.apply())["status"], "completed")
        self.assertEqual(self.journal.load().original, original)
        self.assertEqual([p.service_name for p in self.calls], ["swagger-ui", "traefik", "traefik"])

    async def test_candidate_catalog_blocks_old_forward_resume_but_allows_recovery(self):
        self.fail.add("traefik")
        self.assertEqual((await self.apply())["status"], "partial")
        journal = self.journal.load()
        calls = tuple(self.calls)
        candidate_catalog = NativeComponentCatalog(ROOT).load()
        self.catalog.load.return_value = candidate_catalog
        self.fail.clear()

        with self.assertRaisesRegex(LifecycleStateError, "current catalog no longer qualifies"):
            await self.apply()
        self.assertEqual(self.journal.load(), journal)
        self.assertEqual(tuple(self.calls), calls)

        self.assertEqual((await self.apply(recovery=True))["status"], "recovered")

    async def test_single_service_does_not_update_other_selected_services(self):
        before = self.images["traefik"]
        self.assertEqual((await self.apply(("swagger",)))["status"], "completed")
        self.assertEqual([p.service_name for p in self.calls], ["swagger-ui"])
        self.assertEqual(self.images["traefik"], before)

    async def test_healthy_old_task_cannot_complete_new_native_transition(self):
        self.old_tasks.add("swagger-ui")
        result = await self.apply()
        self.assertNotEqual(result["status"], "completed")
        self.assertEqual([p.service_name for p in self.calls], ["swagger-ui"])
        current = next(c for c in self.manifests.load().manifest.components if c.component_id == "swagger-ui")
        original = next(c for c in self.original.components if c.component_id == "swagger-ui")
        self.assertEqual(current.desired, original.desired)
