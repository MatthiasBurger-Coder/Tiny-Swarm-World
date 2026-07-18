import unittest

from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS


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

        self.assertFalse(
            [
                contract.image_ref
                for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS
                if contract.tag == "latest"
            ]
        )
