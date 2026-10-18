"""Selected artifact contracts preserve actual image publication and verification."""
import os
import asyncio
import unittest
from unittest.mock import Mock, patch

from tiny_swarm_world.application.services.artifacts.workflows import ArtifactWorkflowStatus
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure import composition_artifacts as artifacts


class TestSelectiveArtifacts(unittest.TestCase):
    def build(self, selected):
        return artifacts.build_lxc_artifact_services(
            backend=ManagedLxcBackend.INCUS, resolved_services=selected,
        )

    def test_minimal_selection_omits_nexus_and_prepares_real_public_contracts(self):
        publisher = Mock()
        publisher.image_available.return_value = True
        with (
            patch.object(artifacts, "LxcContainerImagePublisher", return_value=publisher),
            patch.object(artifacts, "_operator_secret_value") as secret,
            patch.object(artifacts, "LxcNexusHttpClient") as nexus,
        ):
            services = self.build(("incus", "portainer"))
            bootstrap = asyncio.run(services.workflows.prepare.run_bootstrap())
            self.assertEqual(ArtifactWorkflowStatus.COMPLETED, bootstrap.status)
            self.assertFalse(bootstrap.executed)
            publisher.publish_image.assert_not_called()
            result = asyncio.run(services.workflows.prepare.run_after_bootstrap(bootstrap))
            verified = asyncio.run(services.workflows.verify.run())
        secret.assert_not_called()
        nexus.assert_not_called()
        self.assertEqual(ArtifactWorkflowStatus.COMPLETED, result.status)
        self.assertEqual(ArtifactWorkflowStatus.COMPLETED, verified.status)
        self.assertEqual(
            ["portainer", "portainer-agent"],
            [call.args[0].build_context for call in publisher.publish_image.call_args_list],
        )
        self.assertEqual(4, publisher.image_available.call_count)

    def test_native_swagger_and_sonarqube_component_bundles_are_complete(self):
        services = self.build(("incus", "portainer", "swagger", "sonarqube"))
        self.assertEqual(
            {"portainer", "portainer-agent", "swagger-editor", "swagger-ui", "swagger-nginx",
             "swagger-api", "sonarqube", "sonarqube-postgres"},
            {step.contract.build_context for step in services.workflows.prepare.steps},
        )
        self.assertEqual((), services.workflows.prepare.bootstrap_steps)

    def test_selected_public_image_failure_still_blocks_prepare(self):
        publisher = Mock()
        publisher.image_available.return_value = False
        with patch.object(artifacts, "LxcContainerImagePublisher", return_value=publisher):
            services = self.build(("incus", "portainer"))
            bootstrap = asyncio.run(services.workflows.prepare.run_bootstrap())
            result = asyncio.run(services.workflows.prepare.run_after_bootstrap(bootstrap))
        self.assertEqual(ArtifactWorkflowStatus.FAILED_TO_VERIFY, result.status)
        self.assertEqual(1, publisher.publish_image.call_count)
        self.assertEqual(1, publisher.image_available.call_count)

    def test_unknown_selection_and_build_without_registry_fail_before_publication(self):
        with patch.object(artifacts, "LxcContainerImagePublisher") as publisher:
            for selected in (("unknown",), ("jenkins",)):
                with self.subTest(selected=selected), self.assertRaises(ValueError):
                    self.build(selected)
        publisher.assert_not_called()

    def test_selected_nexus_keeps_bootstrap_and_excludes_unselected_images(self):
        services = self.build(("incus", "portainer", "nexus"))
        self.assertEqual(5, len(services.workflows.prepare.bootstrap_steps))
        self.assertEqual(
            {"nexus", "portainer", "portainer-agent"},
            {step.contract.build_context for step in services.workflows.prepare.mutation_steps},
        )

    def test_unselected_invalid_image_override_does_not_block_minimal_selection(self):
        with patch.dict(os.environ, {"TSW_JENKINS_IMAGE": "https://invalid/image"}):
            services = self.build(("incus", "portainer"))
        self.assertEqual(2, len(services.workflows.prepare.steps))

    def test_default_empty_bootstrap_remains_blocked(self):
        workflow = artifacts.ArtifactPrepareWorkflow()
        result = asyncio.run(workflow.run_bootstrap())
        self.assertEqual(ArtifactWorkflowStatus.BLOCKED, result.status)
