"""Durable update intent; original transition and installation remain immutable."""
from typing import Literal, Self

from pydantic import model_validator

from tiny_swarm_world.domain.lifecycle.models import Contract, Identifier, InstallationManifest, VersionIdentity
from tiny_swarm_world.domain.lifecycle.update_planning import ComponentUpdatePlan


class UpdateStage(Contract):
    service_id: Identifier
    component_id: Identifier
    source: VersionIdentity
    target: VersionIdentity
    outcome: Literal['pending', 'applying', 'runtime_verified', 'committed', 'recovering', 'recovered', 'failed'] = 'pending'


class UpdateBatch(Contract):
    schema_version: Literal[1] = 1
    original: InstallationManifest
    plan: ComponentUpdatePlan
    stages: tuple[UpdateStage, ...]
    direction: Literal['apply', 'recover'] = 'apply'

    @property
    def settled(self) -> bool:
        expected = 'recovered' if self.direction == 'recover' else 'committed'
        return all(stage.outcome == expected for stage in self.stages)

    @model_validator(mode='after')
    def coherent_intent(self) -> Self:
        if self.plan.status == 'blocked' or not self.plan.services:
            raise ValueError('Batch requires an admitted nonempty plan.')
        if tuple(item.service_id for item in self.plan.services) != self.plan.dependency_order:
            raise ValueError('Batch dependency order differs from service plans.')
        if set(self.plan.requested_services) != set(self.plan.dependency_order):
            raise ValueError('Batch must contain exactly the selected services.')
        selected = set(self.plan.requested_services)
        inventory = {item.component_id for item in self.original.components if item.service_id in selected}
        if not self.stages or {item.component_id for item in self.stages} != inventory:
            raise ValueError('Batch must cover the selected original component inventory.')
        for service in self.plan.services:
            if service.status not in {'planned', 'no_op'} or service.target is None:
                raise ValueError('Batch contains an unsupported service transition.')
            if service.target.qualification != 'qualified-transition':
                raise ValueError('Batch target is not a qualified image transition.')
            if any(change.target != service.target.versions.get(change.component_id) for change in service.components):
                raise ValueError('Component targets differ from the qualified service bundle.')
        expected = [(item.service_id, change.component_id, change.desired, change.target)
                    for item in self.plan.services for change in item.components]
        actual = [(item.service_id, item.component_id, item.source, item.target) for item in self.stages]
        if actual != expected or len({item.component_id for item in self.stages}) != len(self.stages):
            raise ValueError('Stages differ from the complete original transition.')
        originals = {item.component_id: item for item in self.original.components}
        for stage in self.stages:
            component = originals.get(stage.component_id)
            if component is None or component.service_id != stage.service_id or component.desired != stage.source:
                raise ValueError('Stage source differs from the original installation.')
        return self
