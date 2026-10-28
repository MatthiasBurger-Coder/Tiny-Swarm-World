"""Fixed Classic release policies consumed by the native catalog; live proof is separate."""
from tiny_swarm_world.domain.lifecycle.models import (
    ComponentUpdateTarget, ComponentUpdateTransition, ServiceDefinition, VersionIdentity,
)


# Linux/amd64 child manifests, not multiarch indexes. See W09 transition evidence.
_TRAEFIK_SOURCE = "580f70e21a5b63503dcbd5690b432b0e78b056e931a1738a5ca2d997bd08bc47"
_TRAEFIK_TARGET = "e5491c6c7073c18a2fa8ae48196630d64894b41d877aca1babe4a3ad98bd5cba"
_SWAGGER_SOURCE = "9f5fb4ffc28ad30a01e7fd936203d69e21dcfc8cb565145fc85c11976776cfd2"
_SWAGGER_TARGET = "b96d57e3c8c658b2c83ce11e0d87a7ccc7aedcdc20eccd7e83d67dca857a5a27"
_SWAGGER_RETAINED = {
    "swagger-editor": ("swaggerapi/swagger-editor", "337d8cf1d92c803bb7a1b47e6953cf21d8cce0da1c7959dc1eed3ebc7745c50a"),
    "swagger-api": ("danielgtaylor/apisprout", "6c07143937e57095d8478efc8ab7eab52b44e67c7673285f8c0a2bf4a7b137ad"),
    "swagger-nginx": ("nginx", "3bcf852aed06467cf075c6105892e4d5a6ebbbafa0ce22d35062db9e90ddef4c"),
}


def _identity(repository: str, digest: str) -> VersionIdentity:
    # Execution references digests; tags/upstream versions are not runtime observations.
    return VersionIdentity(image_repository=repository, image_digest="sha256:" + digest)


def with_stack_transition(service: ServiceDefinition) -> ServiceDefinition:
    """Admit only the two reviewed stateless transitions; preserve all native defaults."""
    if service.service_id == "traefik":
        target_id = "traefik-3-7-5"
        sources = {"traefik": _identity("traefik", _TRAEFIK_SOURCE)}
        targets = {"traefik": _identity("traefik", _TRAEFIK_TARGET)}
    elif service.service_id == "swagger":
        target_id = "swagger-ui-5-32-7"
        retained = {name: _identity(*identity) for name, identity in _SWAGGER_RETAINED.items()}
        sources = {**retained, "swagger-ui": _identity("swaggerapi/swagger-ui", _SWAGGER_SOURCE)}
        targets = {**retained, "swagger-ui": _identity("swaggerapi/swagger-ui", _SWAGGER_TARGET)}
    else:
        return service
    target = ComponentUpdateTarget(
        target_id=target_id, versions=targets, qualification="candidate-transition",
        metadata_source="w09-pinned-release-policy", presets=service.presets,
    )
    transition = ComponentUpdateTransition(
        target_id=target_id, source_versions=sources, migrations=(), backup_required=False,
        availability_impact="Selected stateless service restarts; routing/UI requests may be unavailable during bounded convergence.",
        recovery_limit="Original pinned images only; retain mounted configuration and protected host baseline. Image rollback is not data restore. Historical bounded W09 live results cover these pinned transitions; this publication includes no new live verification. Overall W09 acceptance remains open.",
    )
    return ServiceDefinition.model_validate({
        **service.model_dump(), "migration_policy": "explicit-transitions",
        "update_targets": (*service.update_targets, target), "update_transitions": (transition,),
    })
