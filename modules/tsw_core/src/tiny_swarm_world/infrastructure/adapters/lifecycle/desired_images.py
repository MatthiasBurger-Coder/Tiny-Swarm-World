"""Share committed desired image pins across deployment, setup and artifacts."""
from collections.abc import Mapping
from pathlib import Path

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.models import VersionIdentity
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import local_state_file


def effective_image_environment(environment: Mapping[str, str], root: Path, *,
                                transition_overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT

    result = dict(environment)
    snapshot = JsonManifestRepository(local_state_file(root=root, relative_path='installation/manifest.json')).load()
    if snapshot.manifest is not None:
        references = {item.reference for item in snapshot.manifest.configuration_references
                      if item.key == 'component-update.' + item.reference and item.source == 'managed_default'}
        for component in snapshot.manifest.components:
            if component.component_id not in references:
                continue
            name = IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT.get(component.component_id)
            version = component.desired
            if name is None or not version.image_repository or not version.image_digest:
                raise LifecycleStateError('Committed component image pin is invalid; inspect installation state.')
            pin = version.image_repository + '@' + version.image_digest
            if result.get(name, '').strip() and result[name].strip() != pin:
                raise LifecycleStateError('Image override conflicts with committed desired state; use component update/recovery.')
            result[name] = pin
    result.update(transition_overrides or {})
    return result


def require_settled_updates(root: Path) -> None:
    from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_journal import JsonPortainerJournal

    checkpoint = JsonPortainerJournal(local_state_file(root=root, relative_path='installation/portainer-upgrade.json')).load()
    if checkpoint is not None and not checkpoint.settled:
        raise LifecycleStateError('Portainer upgrade incomplete; recover the gateway before setup/deployment.')
    batch = JsonUpdateJournal(local_state_file(root=root, relative_path='installation/component-update.json')).load()
    if batch is not None and not batch.settled:
        raise LifecycleStateError('Component runtime/configuration update is incomplete; resume or recover the original selection before setup/deployment.')


def require_settled_product(root: Path) -> None:
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal import JsonProductJournal

    checkpoint = JsonProductJournal(local_state_file(root=root, relative_path='installation/product-upgrade.json')).load()
    if checkpoint is not None and checkpoint.stage != 'completed':
        raise LifecycleStateError('Product upgrade incomplete; resume it before setup/deployment.')


def effective_component_inventory(catalog, resolved_services, existing, root):
    """Use the same committed pins when checking retained setup components."""
    from tiny_swarm_world.domain.artifacts.container_image_contract import DEFAULT_CONTAINER_IMAGE_CONTRACTS
    from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import resolve_container_image_contracts
    import os

    components = tuple(item for service in catalog.load().services
                       if service.service_id in resolved_services for item in service.components)
    contexts = {item.component_id for item in components}
    contracts = resolve_container_image_contracts(tuple(item for item in DEFAULT_CONTAINER_IMAGE_CONTRACTS
                                                       if item.build_context in contexts), effective_image_environment(os.environ, root))
    versions = {item.build_context: VersionIdentity(
        image_repository=item.image_name, image_tag=None if item.tag.startswith("@") else item.tag,
        image_digest=item.tag[1:] if item.tag.startswith("@") else None,
        build_identity=item.tag if item.source == "build" and not item.tag.startswith("@") else None,
    ) for item in contracts}
    retained = {} if existing is None else {item.component_id: item for item in existing.components}
    result = []
    for item in components:
        desired = versions.get(item.component_id, item.desired)
        prior = retained.get(item.component_id)
        if prior is not None and item.component_id in versions and not _same_image(prior.desired, desired):
            raise LifecycleStateError("Effective image inputs differ from installed desired state; use a supported component update or restore matching overrides before adding services.")
        result.append(prior if prior is not None else item.model_copy(update={"desired": desired}))
    return tuple(result)


def _same_image(before: VersionIdentity, after: VersionIdentity) -> bool:
    if before.image_digest and before.image_digest == after.image_digest and before.image_repository == after.image_repository:
        return True
    return all(getattr(before, key) == getattr(after, key)
               for key in ("image_repository", "image_tag", "image_digest", "build_identity"))


def apply_desired_stack_images(stack_environment, environment):
    """Pass pins to actual Compose interpolation, including sibling components."""
    from tiny_swarm_world.domain.update.classic_update import IMAGE_OVERRIDE_ENVIRONMENT_BY_STACK_SERVICE

    pins = dict(IMAGE_OVERRIDE_ENVIRONMENT_BY_STACK_SERVICE, **{'portainer:portainer': 'TSW_PORTAINER_IMAGE', 'portainer:agent': 'TSW_PORTAINER_AGENT_IMAGE'})
    for member, name in pins.items():
        stack, _ = member.split(':', 1)
        if stack in stack_environment and environment.get(name):
            stack_environment[stack][name] = environment[name]
