import unittest

from tiny_swarm_world.domain.inventory import (
    ArtifactRegistryObservedState,
    DesiredInventory,
    DockerObservedState,
    NetworkObservedState,
    ObservedInventory,
    StackObservedState,
    SwarmObservedState,
    VerificationResult,
    VerificationStatus,
    VmDesiredState,
    VmObservedState,
)


class TestVerificationResult(unittest.TestCase):
    def test_verification_status_values_match_workflow_contract(self):
        self.assertEqual(
            {
                "not_checked",
                "verified",
                "failed_to_apply",
                "failed_to_verify",
                "blocked",
                "refused",
            },
            {status.value for status in VerificationStatus},
        )

    def test_result_evidence_is_immutable_and_serializable(self):
        evidence = {"summary": "checked"}
        result = VerificationResult(
            target_id="vm:manager",
            status=VerificationStatus.VERIFIED,
            message="VM exists.",
            evidence=evidence,
        )
        evidence["summary"] = "changed"

        self.assertEqual("checked", result.evidence["summary"])
        self.assertEqual(
            {
                "target_id": "vm:manager",
                "status": "verified",
                "message": "VM exists.",
                "evidence": {"summary": "checked"},
            },
            result.to_dict(),
        )

    def test_result_rejects_raw_command_evidence_keys(self):
        with self.assertRaises(ValueError):
            VerificationResult(
                target_id="command:probe",
                evidence={"stdout": "raw command output"},
            )

    def test_result_rejects_sensitive_evidence_key_names(self):
        with self.assertRaises(ValueError):
            VerificationResult(
                target_id="secret:probe",
                evidence={"password_value": "redacted"},
            )

    def test_result_rejects_raw_or_sensitive_evidence_values(self):
        raw_values = (
            "stdout: secret output",
            "docker swarm join --token hidden",
            "PASSWORD=value",
            "line one\nline two",
        )

        for raw_value in raw_values:
            with self.subTest(raw_value=raw_value):
                with self.assertRaises(ValueError):
                    VerificationResult(
                        target_id="command:probe",
                        evidence={"summary": raw_value},
                    )


class TestInventoryModels(unittest.TestCase):
    def test_desired_inventory_contains_vm_desired_state(self):
        inventory = DesiredInventory(
            vms=(
                VmDesiredState(
                    name="tsw-manager-1",
                    role="manager",
                    image="ubuntu:24.04",
                    memory="4G",
                    disk="20G",
                    networks=("control",),
                    stacks=("portainer",),
                ),
            ),
            expected_stacks=("portainer",),
            expected_artifact_registries=("nexus",),
        )

        round_tripped = DesiredInventory.from_dict(inventory.to_dict())

        self.assertEqual(inventory, round_tripped)
        self.assertEqual(("control",), round_tripped.vms[0].networks)

    def test_observed_inventory_contains_runtime_state_and_verification(self):
        verification = VerificationResult(
            target_id="vm:tsw-manager-1",
            status=VerificationStatus.VERIFIED,
            message="VM listed.",
            evidence={"probe": "multipass-list-summary"},
        )
        inventory = ObservedInventory(
            vms=(
                VmObservedState(
                    name="tsw-manager-1",
                    status="running",
                    role="manager",
                    ip_addresses=("10.0.0.10",),
                    verification=verification,
                ),
            ),
            networks=(
                NetworkObservedState(
                    name="control",
                    status="present",
                    addresses=("10.0.0.0/24",),
                ),
            ),
            docker=DockerObservedState(installed=True, version="26.1", status="ready"),
            swarm=SwarmObservedState(
                active=True,
                node_count=3,
                manager_count=1,
                status="ready",
            ),
            stacks=(
                StackObservedState(
                    name="portainer",
                    status="running",
                    services=("agent", "ui"),
                ),
            ),
            artifact_registries=(
                ArtifactRegistryObservedState(
                    name="nexus",
                    endpoint="http://127.0.0.1:8081",
                    status="reachable",
                ),
            ),
            verification_results=(verification,),
        )

        round_tripped = ObservedInventory.from_dict(inventory.to_dict())

        self.assertEqual(inventory, round_tripped)
        self.assertEqual(VerificationStatus.VERIFIED, round_tripped.vms[0].verification.status)

    def test_inventory_collection_fields_reject_plain_strings(self):
        with self.assertRaises(ValueError):
            VmDesiredState(name="tsw-manager-1", networks="control")


if __name__ == "__main__":
    unittest.main()
