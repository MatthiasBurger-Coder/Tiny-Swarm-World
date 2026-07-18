import unittest

from tiny_swarm_world.application.services.artifacts.ensure_container_image import (
    EnsureContainerImage,
)
from tiny_swarm_world.domain.artifacts import ContainerImageContract
from tiny_swarm_world.domain.inventory import VerificationStatus


class TestEnsureContainerImage(unittest.IsolatedAsyncioTestCase):
    async def test_publishes_image_through_port(self):
        publisher = _FakeImagePublisher(available=True)
        contract = ContainerImageContract("127.0.0.1:13500/jenkins", "latest", "jenkins")
        service = EnsureContainerImage(publisher, contract)

        await service.run()

        self.assertEqual([contract], publisher.published)

    async def test_verify_confirms_image_availability_without_secret_payloads(self):
        publisher = _FakeImagePublisher(available=True)
        contract = ContainerImageContract("127.0.0.1:13500/jenkins", "latest", "jenkins")
        service = EnsureContainerImage(publisher, contract)

        verification = await service.verify()

        self.assertEqual(VerificationStatus.VERIFIED, verification.status)
        self.assertEqual(verification.target_id, "artifacts:jenkins-image")
        self.assertEqual(verification.evidence["image_ref"], "127.0.0.1:13500/jenkins:latest")
        self.assertNotIn("password", str(verification.to_dict()).lower())


class _FakeImagePublisher:
    def __init__(self, available: bool):
        self.available = available
        self.published: list[ContainerImageContract] = []

    def publish_image(self, contract: ContainerImageContract) -> None:
        self.published.append(contract)

    def image_available(self, contract: ContainerImageContract) -> bool:
        return self.available
