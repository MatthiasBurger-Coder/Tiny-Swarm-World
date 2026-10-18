"""Project the single logical Classic catalog from authoritative native assets."""
from pathlib import Path
import re

import yaml

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.artifacts.container_image_contract import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.domain.deployment.service_stack_contract import service_stack_contracts_for_profile
from tiny_swarm_world.domain.lifecycle.models import (
    ComponentCatalog, ComponentState, ResourceRequirements, ServiceDefinition, VersionIdentity,
)

# Only logical dependency/policy metadata lives here. Image/build versions remain
# owned by ContainerImageContract; membership/readiness by ServiceStackContract.
_DEPENDENCIES = {
    "portainer": ("incus",), "traefik": ("portainer",), "nexus": ("portainer",),
    "jenkins": ("portainer", "nexus"), "pulsar": ("portainer",),
    "sonarqube": ("portainer",), "swagger": ("portainer",),
    "infisical": ("portainer",), "service-access": ("portainer", "nexus", "infisical", "traefik"),
}
_STATEFUL = {"portainer", "nexus", "jenkins", "pulsar", "sonarqube", "infisical"}


class NativeComponentCatalog:
    def __init__(self, repository_root: Path):
        self.root = repository_root

    def load(self) -> ComponentCatalog:
        try:
            return self._load()
        except (OSError, UnicodeError, ValueError, TypeError, KeyError, yaml.YAMLError):
            raise LifecycleStateError(
                "Catalog/native asset mismatch; restore matching Compose and image contracts before planning."
            ) from None

    def _load(self) -> ComponentCatalog:
        services = [ServiceDefinition(
            service_id="incus", kind="host-prerequisite", mandatory=True,
            dependencies=(), capabilities=("managed-lxc",), components=(ComponentState(
                component_id="incus", service_id="incus", desired=VersionIdentity(),
            ),), resources=ResourceRequirements(), native_asset=None,
            presets=("default", "service-access"), lifecycle_owner="host-operator",
            backup_policy="not-applicable",
        )]
        for stack in service_stack_contracts_for_profile("service-access"):
            relative = f"infra/config/compose/{stack.stack_name}/docker-compose.yml"
            payload = yaml.safe_load((self.root / relative).read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("services"), dict):
                raise ValueError("Invalid Compose services")
            native = payload["services"]
            for item in native.values():
                _validate_native_service(item)
            if not set(stack.required_services) <= native.keys():
                raise ValueError("Readiness membership drift")
            components = tuple(self._component(stack.stack_name, item) for item in native.values())
            resources = {name: item.get("deploy", {}).get("resources", {}) for name, item in native.items()}
            services.append(ServiceDefinition(
                service_id=stack.stack_name,
                kind="managed-foundation" if stack.stack_name == "portainer" else "stack",
                mandatory=stack.stack_name == "portainer", dependencies=_DEPENDENCIES[stack.stack_name],
                capabilities=("docker-swarm", "shared-overlay"), components=components,
                resources=ResourceRequirements(declared=resources), native_asset=relative,
                presets=(("service-access",) if stack.stack_name in {"infisical", "service-access"}
                         else ("default", "service-access")),
                lifecycle_owner="portainer-adapter" if stack.stack_name == "portainer" else "stack-update",
                backup_policy=("required-before-stateful-transition" if stack.stack_name in _STATEFUL
                               else "not-applicable"),
            ))
        catalog = ComponentCatalog(services=tuple(sorted(services, key=lambda item: item.service_id)))
        identities = [component.component_id for service in services for component in service.components]
        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate component identities")
        used = {component.component_id for service in services for component in service.components} - {"incus"}
        if used != {image.build_context for image in DEFAULT_CONTAINER_IMAGE_CONTRACTS}:
            raise ValueError("Unconsumed image contracts")
        return catalog

    @staticmethod
    def _component(service_id: str, native: dict[str, object]) -> ComponentState:
        image = native["image"]
        if not isinstance(image, str):
            raise ValueError("Invalid image")
        match = re.fullmatch(r"\$\{TSW_[A-Z0-9_]+:-([^{}]+)\}", image)
        image = match.group(1) if match else image
        matches = [item for item in DEFAULT_CONTAINER_IMAGE_CONTRACTS if item.image_ref == image]
        if len(matches) != 1:
            raise ValueError("Ambiguous native image")
        contract = matches[0]
        return ComponentState(
            component_id=contract.build_context, service_id=service_id,
            desired=VersionIdentity(
                image_repository=contract.image_name,
                image_tag=None if contract.tag.startswith("@") else contract.tag,
                image_digest=contract.tag[1:] if contract.tag.startswith("@") else None,
                build_identity=contract.tag if contract.source == "build" else None,
            ),
        )


def _validate_native_service(item: object) -> None:
    if not isinstance(item, dict) or not isinstance(item.get("deploy", {}), dict):
        raise ValueError("Invalid Compose service")
    resources = item.get("deploy", {}).get("resources", {})
    if not isinstance(resources, dict):
        raise ValueError("Invalid resource declarations")
