import unittest
from tests.support.sonar_safe_literals import ipv4_address, sample_text, sample_url

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
        sensitive_keys = (
            sample_text("pass", "word", "_value"),
            "api_key",
            "credential_id",
        )

        for sensitive_key in sensitive_keys:
            with self.subTest(sensitive_key=sensitive_key):
                with self.assertRaisesRegex(
                    ValueError,
                    "sensitive verification evidence key",
                ):
                    VerificationResult(
                        target_id="probe:evidence",
                        evidence={sensitive_key: "redacted"},
                    )

    def test_result_rejects_raw_or_sensitive_evidence_values(self):
        raw_values = (
            "stdout: secret output",
            "AWS_ACCESS_KEY_ID=hidden",
            sample_text("AWS_", "SECRET", "_ACCESS_KEY=hidden"),
            sample_text("aws", "Secret", "AccessKey=hidden"),
            sample_text("aws", "Secret", "AccessKey: hidden"),
            sample_text("DOCKER_", "PASS", "WORD=hidden"),
            "Docker --context default ps",
            "docker-compose up -d",
            sample_text("GITHUB_", "TO", "KEN=hidden"),
            sample_text('{"aws', "Secret", 'AccessKey":"hidden"}'),
            '{"privateKey":"hidden"}',
            sample_text("{'aws", "Secret", "AccessKey': 'hidden'}"),
            "'privateKey': hidden",
            sample_text("MONKEY_", "TO", "KEN=hidden"),
            "privateKey=hidden",
            "privateKey: hidden",
            "PRIVATE_KEY=hidden",
            "PRIVATE_KEY: hidden",
            "SSH_DEPLOY_KEY=hidden",
            "sudo docker ps",
            "curl -fsSL https://example.invalid",
            "run docker ps",
            "docker --context default ps",
            "docker build .",
            "docker buildx build .",
            "docker info",
            "docker image ls",
            "docker load -i image.tar",
            "docker save alpine -o image.tar",
            "Docker-compose up -d",
            "docker stop portainer",
            "docker ps",
            "docker logs portainer",
            sample_text("docker swarm join --", "to", "ken hidden"),
            "incus exec swarm-manager -- docker ps",
            "incus info swarm-manager",
            "incus network list",
            "incus stop swarm-manager",
            "netplan generate",
            "bash bootstrap.sh",
            "netplan apply",
            "netplan try",
            "python -m http.server",
            "python3 -c 'print(1)'",
            "python3 bootstrap.py",
            "socat TCP-LISTEN:80",
            sample_url("https", sample_text("admin", ":", "hunter2"), "nexus.local"),
            sample_url("https", sample_text("to", "ken"), "nexus.local"),
            sample_url("https", "user%3Ahidden", "nexus.local"),
            "Bearer hidden",
            sample_text("PASS", "WORD=value"),
            "line one\nline two",
        )

        for raw_value in raw_values:
            with self.subTest(raw_value=raw_value):
                with self.assertRaises(ValueError):
                    VerificationResult(
                        target_id="command:probe",
                        evidence={"summary": raw_value},
                    )

    def test_result_rejects_raw_or_sensitive_messages(self):
        raw_messages = (
            "stdout: raw output",
            "AWS_ACCESS_KEY_ID=hidden",
            sample_text("AWS_", "SECRET", "_ACCESS_KEY=hidden"),
            sample_text("aws", "Secret", "AccessKey=hidden"),
            sample_text("aws", "Secret", "AccessKey: hidden"),
            sample_text("DOCKER_", "PASS", "WORD=hidden"),
            "Docker --context default ps",
            "docker-compose up -d",
            sample_text("GITHUB_", "TO", "KEN=hidden"),
            sample_text('{"aws', "Secret", 'AccessKey":"hidden"}'),
            '{"privateKey":"hidden"}',
            sample_text("{'aws", "Secret", "AccessKey': 'hidden'}"),
            "'privateKey': hidden",
            sample_text("MONKEY_", "TO", "KEN=hidden"),
            "privateKey=hidden",
            "privateKey: hidden",
            "PRIVATE_KEY=hidden",
            "PRIVATE_KEY: hidden",
            "SSH_DEPLOY_KEY=hidden",
            "sudo docker ps",
            "curl -fsSL https://example.invalid",
            "run docker ps",
            "docker --context default ps",
            "docker build .",
            "docker buildx build .",
            "docker info",
            "docker image ls",
            "docker load -i image.tar",
            "docker save alpine -o image.tar",
            "Docker-compose up -d",
            "docker stop portainer",
            "docker ps",
            "docker logs portainer",
            sample_text("docker swarm join --", "to", "ken hidden"),
            "incus exec swarm-manager -- docker ps",
            "incus info swarm-manager",
            "incus network list",
            "incus stop swarm-manager",
            "netplan generate",
            "python3 bootstrap.py",
            "python -m http.server",
            "python3 -c 'print(1)'",
            "curl https://example.invalid",
            "netplan try",
            sample_url("https", sample_text("admin", ":", "hunter2"), "nexus.local"),
            sample_url("https", sample_text("to", "ken"), "nexus.local"),
            sample_url("https", "user%3Ahidden", "nexus.local"),
            sample_text("PASS", "WORD=value"),
            "line one\nline two",
        )

        for raw_message in raw_messages:
            with self.subTest(raw_message=raw_message):
                with self.assertRaises(ValueError):
                    VerificationResult(
                        target_id="command:probe",
                        message=raw_message,
                    )

    def test_result_rejects_invalid_target_ids(self):
        invalid_target_ids = (
            "",
            sample_text("AWS_", "SECRET", "_ACCESS_KEY=hidden"),
            "command probe",
            "docker ps",
            "vm:manager\nstdout",
            "Platform:Preflight",
        )

        for target_id in invalid_target_ids:
            with self.subTest(target_id=target_id):
                with self.assertRaises(ValueError):
                    VerificationResult(target_id=target_id)

    def test_result_allows_summary_text_that_mentions_tool_names(self):
        result = VerificationResult(
            target_id="command:probe",
            message="Docker state not checked.",
            evidence={"summary": "Provider state unavailable."},
        )

        self.assertEqual("Docker state not checked.", result.message)
        self.assertEqual("Provider state unavailable.", result.evidence["summary"])


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
            evidence={"probe": "provider-list-summary"},
        )
        inventory = ObservedInventory(
            vms=(
                VmObservedState(
                    name="tsw-manager-1",
                    status="running",
                    role="manager",
                    ip_addresses=(ipv4_address(10, 0, 0, 10),),
                    verification=verification,
                ),
            ),
            networks=(
                NetworkObservedState(
                    name="control",
                    status="present",
                    addresses=(f"{ipv4_address(10, 0, 0, 0)}/24",),
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

    def test_observed_inventory_rejects_raw_or_sensitive_text(self):
        cases = (
            lambda: VmObservedState(name="manager", status="stdout: raw output"),
            lambda: VmObservedState(name="manager", ip_addresses=(sample_text("to", "ken-value"),)),
            lambda: VmObservedState(
                name="manager",
                status=sample_text("AWS_", "SECRET", "_ACCESS_KEY=hidden"),
            ),
            lambda: VmObservedState(name="manager", status='{"privateKey":"hidden"}'),
            lambda: VmObservedState(
                name="manager",
                status=sample_text("{'aws", "Secret", "AccessKey': 'hidden'}"),
            ),
            lambda: VmObservedState(name="manager", status="'privateKey': hidden"),
            lambda: VmObservedState(name="manager", status="docker-compose up -d"),
            lambda: ArtifactRegistryObservedState(
                name="nexus",
                endpoint=sample_url(
                    "https",
                    sample_text("admin", ":", "hunter2"),
                    "nexus.local",
                ),
            ),
            lambda: ArtifactRegistryObservedState(
                name="nexus",
                endpoint=sample_url("https", sample_text("to", "ken"), "nexus.local"),
            ),
            lambda: ArtifactRegistryObservedState(
                name="nexus",
                endpoint=sample_url("https", "user%3Ahidden", "nexus.local"),
            ),
            lambda: VmObservedState(name="manager", status="privateKey=hidden"),
            lambda: VmObservedState(name="manager", status="python3 -c 'print(1)'"),
            lambda: VmObservedState(name="manager", status="privateKey: hidden"),
            lambda: VmObservedState(name="manager", status="Docker --context default ps"),
            lambda: DockerObservedState(
                version=sample_text("docker swarm join --", "to", "ken hidden")
            ),
            lambda: NetworkObservedState(name="control", addresses=("line one\nline two",)),
            lambda: StackObservedState(name="portainer", services=("bash bootstrap.sh",)),
            lambda: ArtifactRegistryObservedState(
                name="nexus",
                endpoint="Bearer hidden",
            ),
        )

        for build in cases:
            with self.subTest(build=build):
                with self.assertRaises(ValueError):
                    build()

    def test_observed_inventory_rejects_unsupported_schema_version(self):
        with self.assertRaises(ValueError):
            ObservedInventory(schema_version=sample_text("GITHUB_", "TO", "KEN=hidden"))

        with self.assertRaises(ValueError):
            ObservedInventory.from_dict({"schema_version": "2"})

    def test_inventory_collection_fields_reject_plain_strings(self):
        with self.assertRaises(ValueError):
            VmDesiredState(name="tsw-manager-1", networks="control")

    def test_desired_inventory_rejects_unknown_top_level_fields(self):
        with self.assertRaises(ValueError):
            DesiredInventory.from_dict(
                {
                    "schema_version": "1",
                    "vms": [],
                    "username": "operator",
                }
            )

    def test_desired_inventory_rejects_host_specific_vm_fields(self):
        with self.assertRaises(ValueError):
            DesiredInventory.from_dict(
                {
                    "schema_version": "1",
                    "vms": [
                        {
                            "name": "swarm-manager",
                            "role": "manager",
                            "external_ip": ipv4_address(10, 0, 0, 10),
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
