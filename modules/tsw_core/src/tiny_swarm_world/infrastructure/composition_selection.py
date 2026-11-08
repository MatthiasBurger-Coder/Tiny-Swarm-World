"""Selection projections shared by existing Classic composition boundaries."""
from dataclasses import replace
from typing import TypedDict

from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.preflight import ARTIFACT_READINESS_TARGETS, default_setup_manifest
from tiny_swarm_world.domain.preflight.preflight_configuration import PreflightConfiguration, RequiredPort, RequiredSecret
from tiny_swarm_world.domain.configuration.secret_manifest import SecretManifestEntry


class SelectionOptions(TypedDict, total=False):
    resolved_services: tuple[str, ...]


def selection_options(resolved_services: tuple[str, ...] | None) -> SelectionOptions:
    return {} if resolved_services is None else {"resolved_services": resolved_services}


def includes_service(resolved_services: tuple[str, ...] | None, service: str) -> bool:
    return resolved_services is None or service in resolved_services


def selected_preflight(configuration: PreflightConfiguration, profile: ServiceStackProfile | str,
                       resolved_services: tuple[str, ...] | None) -> PreflightConfiguration:
    if resolved_services is None:
        return configuration
    manifest = default_setup_manifest(service_profile=profile, resolved_services=resolved_services)
    keys = {secret.name for secret in manifest.required_secrets}
    return replace(
        configuration, setup_manifest=manifest,
        required_ports=tuple(RequiredPort(item.port, item.service) for item in manifest.required_ports if item.host_preflight_required),
        required_secrets=tuple(RequiredSecret(item.name, item.service, item.value_kind) for item in manifest.required_secrets),
        static_secret_defaults=tuple(item for item in configuration.static_secret_defaults if item.name in keys),
    )


def artifact_targets(resolved_services: tuple[str, ...] | None) -> tuple[str, ...]:
    if resolved_services is None:
        return ARTIFACT_READINESS_TARGETS
    excluded = set() if "nexus" in resolved_services else {"registry:endpoint", "nexus:endpoint", "nexus:repositories"}
    if not {"jenkins", "service-access"} & set(resolved_services):
        excluded.add("build:inputs")
    return tuple(name for name in ARTIFACT_READINESS_TARGETS if name not in excluded)


def selected_secret_entries(entries: tuple[SecretManifestEntry, ...], environment: dict[str, dict[str, str]],
                            resolved_services: tuple[str, ...] | None) -> tuple[SecretManifestEntry, ...]:
    if resolved_services is None:
        return entries
    selected_keys = {key for values in environment.values() for key in values}
    selected_keys.add("TSW_PORTAINER_ADMIN_PASSWORD")
    if "nexus" in resolved_services:
        selected_keys.add("TSW_NEXUS_ADMIN_PASSWORD")
    if "sonarqube" in resolved_services:
        selected_keys.add("TSW_SONARQUBE_ADMIN_PASSWORD")
    return tuple(item for item in entries if item.key in selected_keys)


def uses_infisical_setup(profile: ServiceStackProfile, update_stack_name: str | None,
                        resolved_services: tuple[str, ...] | None) -> bool:
    return (profile is ServiceStackProfile.SERVICE_ACCESS and update_stack_name is None
            and includes_service(resolved_services, "infisical"))


def persisted_runtime_selection(profile: ServiceStackProfile | str, resolved_services: tuple[str, ...] | None
                                ) -> tuple[ServiceStackProfile | str, tuple[str, ...] | None]:
    """Reuse validated desired selection for standalone reconcile/verify callers."""
    if resolved_services is not None:
        return profile, resolved_services
    from .composition_lifecycle import build_installation_lifecycle_service
    from tiny_swarm_world.application.services.service_selection import ServiceSelectionService

    lifecycle = build_installation_lifecycle_service()
    if lifecycle.manifests.load().manifest is None:
        return profile, None
    plan = ServiceSelectionService(lifecycle.manifests, lifecycle.catalog).preview()
    return plan.service_preset, plan.resolved_services


def artifact_contexts(root, resolved_services: tuple[str, ...]) -> set[str]:
    from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog

    services = {service.service_id: service for service in NativeComponentCatalog(root).load().services}
    if not set(resolved_services) <= services.keys():
        raise ValueError("Unknown selected artifact service.")
    return {component.component_id for name in resolved_services for component in services[name].components}


def persisted_setup_plan():
    from .composition_lifecycle import build_installation_lifecycle_service
    from tiny_swarm_world.application.services.service_selection import ServiceSelectionService

    lifecycle = build_installation_lifecycle_service()
    if lifecycle.manifests.load().manifest is None:
        return None
    return ServiceSelectionService(lifecycle.manifests, lifecycle.catalog).preview()


def scoped_stack_environment(environment: dict[str, dict[str, str]], selected: tuple[str, ...] | None) -> dict[str, dict[str, str]]:
    return {name: values for name, values in environment.items() if includes_service(selected, name)}


def needs_registry_images(selected: tuple[str, ...] | None) -> bool:
    return selected is None or bool({"jenkins", "service-access"} & set(selected))
