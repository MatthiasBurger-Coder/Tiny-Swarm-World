"""Remove only Swagger's external publication for explicit internal mode."""
from typing import Any

from tiny_swarm_world.application.ports.repositories.port_repository_failure import RepositoryConfigurationError


def internal_swagger_payload(payload: dict[str, Any]) -> None:
    networks = payload.get('networks', {})
    if not isinstance(networks, dict):
        raise RepositoryConfigurationError('Internal Swagger requires declared Swarm networks.')
    for network, definition in networks.items():
        if network == 'host' or (isinstance(definition, dict) and
                (definition.get('driver') == 'host' or definition.get('name') == 'host')):
            raise RepositoryConfigurationError('Internal Swagger cannot use a host network.')
    for service in payload['services'].values():
        attached = service.get('networks', ())
        if attached is None:
            attached = ()
        if not isinstance(attached, (dict, list, tuple)):
            raise RepositoryConfigurationError('Internal Swagger networks must be a mapping or list.')
        if 'network_mode' in service or 'host' in attached:
            raise RepositoryConfigurationError('Internal Swagger cannot use a host network.')
        service.pop('ports', None)
        for owner in (service, service.get('deploy', {})):
            if not isinstance(owner, dict):
                raise RepositoryConfigurationError('Internal Swagger labels require a Compose mapping.')
            labels = owner.get('labels')
            if isinstance(labels, dict):
                owner['labels'] = {key: value for key, value in labels.items()
                                   if not str(key).lower().startswith('traefik.')}
            elif isinstance(labels, list):
                owner['labels'] = [value for value in labels
                                   if not str(value).lower().startswith('traefik.')]
            elif labels is not None:
                raise RepositoryConfigurationError('Internal Swagger labels must be a mapping or list.')
