import unittest

from tiny_swarm_world.domain.artifacts import (
    ArtifactImageInventory,
    ArtifactImageRequirement,
    ContainerImageContract,
    DEFAULT_CONTAINER_IMAGE_CONTRACTS,
)


class TestContainerImageContract(unittest.TestCase):
    def test_default_image_contracts_cover_setup_managed_images(self):
        contracts_by_context = {
            contract.build_context: contract
            for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS
        }

        self.assertEqual(
            tuple(contracts_by_context),
            (
                "jenkins",
                "service-access-dashboard",
                "service-access-nginx",
                "infisical",
                "infisical-postgres",
                "infisical-redis",
                "traefik",
                "sonarqube",
                "sonarqube-postgres",
                "swagger-editor",
                "swagger-ui",
                "pulsar",
                "pulsar-manager",
                "pulsar-manager-bootstrap",
                "swagger-nginx",
                "portainer",
                "portainer-agent",
                "nexus",
                "swagger-api",
            ),
        )
        self.assertEqual(
            contracts_by_context["service-access-dashboard"].image_ref,
            "127.0.0.1:13500/service-access-dashboard:0.2.0",
        )
        self.assertEqual(
            contracts_by_context["service-access-nginx"].image_ref,
            "127.0.0.1:13500/service-access-nginx:0.2.0",
        )
        self.assertEqual(contracts_by_context["infisical"].source, "pull")
        self.assertEqual(
            contracts_by_context["infisical"].image_ref,
            "infisical/infisical:v0.159.1",
        )
        self.assertEqual(
            contracts_by_context["infisical-postgres"].image_ref,
            "postgres:14.23-alpine3.23",
        )
        self.assertEqual(
            contracts_by_context["infisical-redis"].image_ref,
            "redis:7.4.9-alpine3.21",
        )
        self.assertEqual(contracts_by_context["traefik"].source, "pull")
        self.assertEqual(contracts_by_context["traefik"].image_ref, "traefik:v3.7.4")
        self.assertEqual(contracts_by_context["sonarqube"].source, "pull")
        self.assertEqual(
            contracts_by_context["sonarqube"].image_ref,
            "sonarqube:26.6.0.123539-community",
        )
        self.assertEqual(contracts_by_context["sonarqube-postgres"].image_ref, "postgres:13.23")
        self.assertEqual(
            contracts_by_context["swagger-editor"].image_ref,
            "swaggerapi/swagger-editor:v5.6.2-unprivileged",
        )
        self.assertEqual(
            contracts_by_context["swagger-ui"].image_ref,
            "swaggerapi/swagger-ui:v5.32.6",
        )
        self.assertEqual(contracts_by_context["pulsar"].image_ref, "apachepulsar/pulsar:3.0.17")
        self.assertEqual(
            contracts_by_context["pulsar-manager"].image_ref,
            "apachepulsar/pulsar-manager:v0.4.0",
        )
        self.assertEqual(
            contracts_by_context["pulsar-manager-bootstrap"].image_ref,
            "python:3.12.13-alpine3.23",
        )
        self.assertEqual(contracts_by_context["swagger-nginx"].image_ref, "nginx:1.29.8-alpine")
        self.assertEqual(contracts_by_context["portainer"].image_ref, "portainer/portainer-ce:2.45.0")
        self.assertEqual(contracts_by_context["portainer-agent"].image_ref, "portainer/agent:2.45.0")
        self.assertEqual(contracts_by_context["nexus"].image_ref, "sonatype/nexus3:3.75.1")
        self.assertEqual(
            contracts_by_context["swagger-api"].image_ref,
            "danielgtaylor/apisprout@sha256:6c07143937e57095d8478efc8ab7eab52b44e67c7673285f8c0a2bf4a7b137ad",
        )

        self.assertFalse(
            [
                contract.image_ref
                for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS
                if contract.tag == "latest"
            ]
        )

    def test_implicit_latest_is_a_static_preflight_failure(self):
        contract = ContainerImageContract("example/image", "latest", "example")

        issues = contract.validation_issues()

        self.assertEqual(("implicit_latest_not_allowed",), tuple(issue.code for issue in issues))

    def test_digest_references_are_rendered_without_a_second_colon(self):
        contract = ContainerImageContract(
            "example/image",
            "@sha256:" + "a" * 64,
            "example",
            source="pull",
        )

        self.assertEqual("example/image@sha256:" + "a" * 64, contract.image_ref)
        self.assertEqual((), contract.validation_issues())

    def test_inventory_accepts_exact_profile_contract_alignment(self):
        contract = ContainerImageContract("example/image", "1.2.3", "example")
        inventory = ArtifactImageInventory(
            profile="default",
            requirements=(
                ArtifactImageRequirement(
                    service_name="example",
                    image_ref=contract.image_ref,
                    build_context="example",
                    source="build",
                ),
            ),
            contracts=(contract,),
        )

        self.assertTrue(inventory.valid)
        self.assertEqual([], inventory.to_dict()["issues"])

    def test_inventory_reports_missing_and_unused_contracts(self):
        deployed = ContainerImageContract("example/deployed", "1.0.0", "deployed")
        unused = ContainerImageContract("example/unused", "1.0.0", "unused")
        inventory = ArtifactImageInventory(
            profile="default",
            requirements=(
                ArtifactImageRequirement(
                    service_name="deployed",
                    image_ref=deployed.image_ref,
                    build_context="deployed",
                ),
                ArtifactImageRequirement(
                    service_name="missing",
                    image_ref="example/missing:1.0.0",
                    build_context="missing",
                ),
            ),
            contracts=(deployed, unused),
        )

        self.assertEqual(
            {"missing_image_contract", "unused_image_contract"},
            {issue.code for issue in inventory.validate()},
        )

    def test_inventory_reports_duplicate_context_and_mismatch(self):
        first = ContainerImageContract("example/first", "1.0.0", "example")
        second = ContainerImageContract("example/first", "1.0.0", "example")
        inventory = ArtifactImageInventory(
            profile="default",
            requirements=(
                ArtifactImageRequirement(
                    service_name="example",
                    image_ref=first.image_ref,
                    build_context="other",
                    source="pull",
                ),
            ),
            contracts=(first, second),
        )

        self.assertEqual(
            {
                "duplicate_logical_build_context",
                "conflicting_image_reference",
                "image_contract_mismatch",
                "image_source_mismatch",
            },
            {issue.code for issue in inventory.validate()},
        )
