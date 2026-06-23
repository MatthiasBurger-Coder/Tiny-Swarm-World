import unittest

from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS


class TestContainerImageContract(unittest.TestCase):
    def test_default_image_contracts_cover_setup_managed_images(self):
        contracts_by_context = {
            contract.build_context: contract
            for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS
        }

        self.assertEqual(
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
                "pulsar-manager-bootstrap",
                "swagger-nginx",
            ),
            tuple(contracts_by_context),
        )
        self.assertEqual(
            "127.0.0.1:13500/service-access-dashboard:latest",
            contracts_by_context["service-access-dashboard"].image_ref,
        )
        self.assertEqual(
            "127.0.0.1:13500/service-access-nginx:latest",
            contracts_by_context["service-access-nginx"].image_ref,
        )
        self.assertEqual("pull", contracts_by_context["infisical"].source)
        self.assertEqual(
            "infisical/infisical:v0.159.1",
            contracts_by_context["infisical"].image_ref,
        )
        self.assertEqual(
            "postgres:14-alpine",
            contracts_by_context["infisical-postgres"].image_ref,
        )
        self.assertEqual(
            "redis:7-alpine",
            contracts_by_context["infisical-redis"].image_ref,
        )
        self.assertEqual("pull", contracts_by_context["traefik"].source)
        self.assertEqual("traefik:v3.7.4", contracts_by_context["traefik"].image_ref)
        self.assertEqual("pull", contracts_by_context["sonarqube"].source)
        self.assertEqual(
            "sonarqube:26.6.0.123539-community",
            contracts_by_context["sonarqube"].image_ref,
        )
        self.assertEqual("postgres:13", contracts_by_context["sonarqube-postgres"].image_ref)
        self.assertEqual(
            "swaggerapi/swagger-editor:v5.6.2-unprivileged",
            contracts_by_context["swagger-editor"].image_ref,
        )
        self.assertEqual(
            "swaggerapi/swagger-ui:v5.32.6",
            contracts_by_context["swagger-ui"].image_ref,
        )
        self.assertEqual(
            "python:3.12-alpine",
            contracts_by_context["pulsar-manager-bootstrap"].image_ref,
        )
        self.assertEqual("nginx:mainline-alpine", contracts_by_context["swagger-nginx"].image_ref)
