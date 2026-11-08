"""Bounded Classic Portainer manager runtime operations."""

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import PortainerObservation, SOURCE_VERSION, TARGET_VERSION, images

from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_topology import inspect_topology


class PortainerInspection:
    def __init__(self, state, api):
        self.state, self.api = state, api

    def inspect(self, *, prepare_upgrade=True):
        services, volume, swarm = inspect_topology(self.state)
        server, agent = services['portainer_portainer'], services['portainer_agent']
        container = server['Spec']['TaskTemplate']['ContainerSpec']
        self.state.volume_path(volume)
        self.api.swarm_id = swarm
        version, endpoints, ownership = self.api.inventory()
        self.api.proof_definition()
        self.state.wait_stack(self.api.proof_stack['Name'])
        if version not in {SOURCE_VERSION, TARGET_VERSION}:
            raise LifecycleStateError('Unsupported Portainer source version; no inferred migration or downgrade.')
        expected = images(version)
        server_image = container['Image']
        agent_image = agent['Spec']['TaskTemplate']['ContainerSpec']['Image']
        for image, key in ((server_image, 'portainer'), (agent_image, 'portainer-agent')):
            # Docker may retain the tag ahead of the resolved digest.
            if image.split('@')[-1] != expected[key].split('@')[-1] or image.split('@')[0].split(':')[0] != expected[key].split('@')[0]:
                raise LifecycleStateError('Server/agent image drift or unsupported image identity.')
        self.state.wait_images(version)
        if prepare_upgrade and version == SOURCE_VERSION:
            for release in (SOURCE_VERSION, TARGET_VERSION):
                for image in images(release).values():
                    self.state.run(f'docker image inspect {image} >/dev/null')
        self.state.run('command -v tar >/dev/null && command -v sha256sum >/dev/null && command -v cp >/dev/null')
        return PortainerObservation(version=version, server_image=server_image, agent_image=agent_image,
                                    volume=volume, server_id=server['ID'], agent_id=agent['ID'], swarm_id=swarm, endpoints=endpoints, ownership=ownership)
