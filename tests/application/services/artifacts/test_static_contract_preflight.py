import asyncio
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from tiny_swarm_world.application.services.artifacts.static_contract_preflight import (
    StaticArtifactContractPreflight,
)
from tiny_swarm_world.application.services.setup import SetupWorkflow, SetupWorkflowPhase
from tiny_swarm_world.domain.artifacts import (
    ArtifactImageInventory,
    ArtifactImageRequirement,
    ContainerImageContract,
)
from tiny_swarm_world.domain.preflight import LiveConsent


class TestStaticArtifactContractPreflight(unittest.TestCase):
    def test_success_checks_build_context_without_invoking_external_clients(self):
        contract = ContainerImageContract("registry.local/example", "1.0.0", "example")
        inventory = ArtifactImageInventory(
            profile="default",
            requirements=(
                ArtifactImageRequirement(
                    service_name="example:worker",
                    image_ref=contract.image_ref,
                    build_context="example",
                    source="build",
                ),
            ),
            contracts=(contract,),
        )
        compose = MagicMock()
        compose.get_image_inventory.return_value = inventory
        compose.get_build_context_path.return_value = Path("/repo/example")
        storage = MagicMock()
        storage.directory_exists.return_value = True

        result = StaticArtifactContractPreflight(compose, storage).run()

        self.assertEqual("PASSED", result.status)
        self.assertEqual("static", result.checks[0].evidence["evidence_scope"])
        compose.get_build_context_path.assert_called_once_with("example")
        storage.directory_exists.assert_called_once_with(Path("/repo/example"))

    def test_missing_build_context_fails_closed_with_safe_remediation(self):
        contract = ContainerImageContract("registry.local/example", "1.0.0", "example")
        inventory = ArtifactImageInventory(
            profile="default",
            requirements=(
                ArtifactImageRequirement(
                    service_name="example:worker",
                    image_ref=contract.image_ref,
                    build_context="example",
                    source="build",
                ),
            ),
            contracts=(contract,),
        )
        compose = MagicMock()
        compose.get_image_inventory.return_value = inventory
        compose.get_build_context_path.return_value = Path("/repo/example")
        storage = MagicMock()
        storage.directory_exists.return_value = False

        result = StaticArtifactContractPreflight(compose, storage).run()

        self.assertEqual("FAILED", result.status)
        check = result.failed_checks[0]
        self.assertIn("build context", check.remediation.lower())
        self.assertEqual("static", check.evidence["evidence_scope"])

    def test_failed_static_phase_stops_later_artifact_phase(self):
        contract = ContainerImageContract("registry.local/example", "1.0.0", "example")
        compose = MagicMock()
        compose.get_image_inventory.return_value = ArtifactImageInventory(
            profile="default",
            requirements=(),
            contracts=(contract,),
        )
        later_phase = MagicMock(return_value={"status": "completed"})
        workflow = SetupWorkflow(
            phases=(
                SetupWorkflowPhase(
                    "artifact contract preflight",
                    StaticArtifactContractPreflight(compose, MagicMock()).run,
                ),
                SetupWorkflowPhase("artifacts prepare", later_phase),
            ),
            live_consent=LiveConsent(live_flag=True, confirmed=True),
        )

        result = asyncio.run(workflow.run())

        self.assertEqual("failed", result.status.value)
        self.assertEqual(2, len(result.phase_results))
        self.assertEqual("not_run", result.phase_results[1].status)
        later_phase.assert_not_called()


if __name__ == "__main__":
    unittest.main()
