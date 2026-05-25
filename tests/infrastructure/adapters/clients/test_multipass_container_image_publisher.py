import unittest
from pathlib import Path

from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.infrastructure.adapters.clients.multipass_container_image_publisher import (
    MultipassContainerImagePublisher,
)


class TestMultipassContainerImagePublisher(unittest.TestCase):
    def test_service_access_image_contexts_are_supported(self):
        publisher = MultipassContainerImagePublisher(
            registry_username="admin",
            registry_password="local-only",
        )

        contexts = {
            "service-access-dashboard": Path("infra/compose/service-access/dashboard"),
            "service-access-nginx": Path("infra/compose/service-access/nginx"),
        }

        for build_context, expected_suffix in contexts.items():
            with self.subTest(build_context=build_context):
                contract = ContainerImageContract(
                    image_name=f"127.0.0.1:5000/{build_context}",
                    tag="latest",
                    build_context=build_context,
                )

                context_path = publisher._context_path(contract)

                self.assertTrue(context_path.as_posix().endswith(expected_suffix.as_posix()))
                self.assertTrue((context_path / "Dockerfile").is_file())
