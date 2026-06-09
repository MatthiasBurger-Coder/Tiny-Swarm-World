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
            ),
            tuple(contracts_by_context),
        )
        self.assertEqual(
            "127.0.0.1:5000/service-access-dashboard:latest",
            contracts_by_context["service-access-dashboard"].image_ref,
        )
        self.assertEqual(
            "127.0.0.1:5000/service-access-nginx:latest",
            contracts_by_context["service-access-nginx"].image_ref,
        )
        self.assertEqual("pull", contracts_by_context["infisical"].source)
        self.assertEqual(
            "infisical/infisical:latest",
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
