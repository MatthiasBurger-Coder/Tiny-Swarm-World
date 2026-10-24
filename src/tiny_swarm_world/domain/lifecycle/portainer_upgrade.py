"""Bounded management-gateway policy; host qualification belongs to W09."""
from typing import Literal

from tiny_swarm_world.domain.lifecycle.models import Contract, Digest, InstallationManifest, VersionIdentity

SOURCE_VERSION = '2.45.0'
TARGET_VERSION = '2.45.1'
TARGET_ID = 'portainer-ce-2.45.1'
_DIGESTS = {
    SOURCE_VERSION: ('511f3f06c96fe3b993ebeaafde311c1959cae73a7ef825dba6397d51b450dffa',
                     'd63bfe57a106070fa5c0e73de0758f33aea018ed3cb6c8610c6663a4ac3a82ba'),
    TARGET_VERSION: ('4d616db18cfeb5dd41a69c0958bc825c84483ea9cde1106eb82a5d26f3bd8b0e',
                     '38bc1dc7b8470eecbd979d444aa5d0a187dacf1245f2b54466f0f25f4c6d9a7c'),
}


def versions(version: str) -> dict[str, VersionIdentity]:
    return {name: VersionIdentity(upstream_version=version, image_repository=repo,
                                 image_tag=version, image_digest='sha256:' + digest)
            for name, repo, digest in zip(('portainer', 'portainer-agent'),
                                         ('portainer/portainer-ce', 'portainer/agent'), _DIGESTS[version])}


def images(version: str) -> dict[str, str]:
    return {name: f'{identity.image_repository}@{identity.image_digest}' for name, identity in versions(version).items()}


class PortainerObservation(Contract):
    version: Literal['2.45.0', '2.45.1']
    server_image: str
    agent_image: str
    volume: str
    server_id: str
    agent_id: str
    swarm_id: str
    endpoints: tuple[str, ...]
    ownership: tuple[str, ...]


class PortainerCheckpoint(Contract):
    operation_id: str
    installation_id: str
    original: InstallationManifest
    before: PortainerObservation
    manifest_token: str
    backup_digest: Digest | None = None
    stage: Literal['admitted', 'backed_up', 'upgrading', 'verified', 'recovering', 'recovered', 'completed'] = 'admitted'

    @property
    def settled(self) -> bool:
        return self.stage in {'completed', 'recovered'}
