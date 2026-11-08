"""Durable management intent contains identities and digests, never Env values."""
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from tiny_swarm_world.domain.lifecycle.models import Contract, Digest, Identifier, PortainerOwnership


class ManagedStackIntent(Contract):
    schema_version: Literal[1] = 1
    installation_id: Annotated[str, Field(min_length=36, max_length=36)]
    operation_id: Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
    stack_name: Identifier
    endpoint_id: int = Field(gt=0)
    target_fingerprint: Digest
    source: PortainerOwnership | None = None
    result: PortainerOwnership | None = None
    created_stack_id: int | None = Field(default=None, gt=0)
    created_resource_control_id: int | None = Field(default=None, gt=0)
    created_ownership_fingerprint: Digest | None = None
    recovery_of: Digest | None = None
    recovery_source: PortainerOwnership | None = None
    phase: Literal['prepared', 'uncertain', 'received', 'verified'] = 'prepared'

    @model_validator(mode='after')
    def identities(self) -> Self:
        from uuid import UUID

        if str(UUID(self.installation_id)) != self.installation_id:
            raise ValueError('Installation identity must be canonical.')
        if not self.operation_id or len(self.operation_id) > 200:
            raise ValueError('Operation identity required.')
        if len({value is None for value in (self.created_stack_id, self.created_resource_control_id, self.created_ownership_fingerprint)}) > 1:
            raise ValueError('Create receipt must bind all known ownership identities together.')
        if (self.recovery_of is None) != (self.recovery_source is None):
            raise ValueError('Recovery must retain both original source and target identity.')
        for value in (self.source, self.result, self.recovery_source):
            if value is not None and value.endpoint_id != self.endpoint_id:
                raise ValueError('Endpoint changed inside managed stack intent.')
        if self.source is not None and self.created_stack_id is not None:
            raise ValueError('An update cannot fabricate a creation receipt.')
        if self.result is not None and self.source is not None and self.result.model_copy(update={
                'definition_fingerprint': self.source.definition_fingerprint}) != self.source:
            raise ValueError('An update cannot change stack/resource ownership identity.')
        if self.result is not None and self.created_stack_id is not None and (
                self.result.stack_id != self.created_stack_id or self.result.resource_control_id != self.created_resource_control_id
                or self.result.ownership_fingerprint != self.created_ownership_fingerprint):
            raise ValueError('Verified ownership differs from the create receipt.')
        if self.recovery_source is not None and self.source is not None and self.recovery_source.model_copy(update={
                'definition_fingerprint': self.source.definition_fingerprint}) != self.source:
            raise ValueError('Recovery cannot change the original ownership identity.')
        if self.result is not None and self.result.definition_fingerprint != self.target_fingerprint:
            raise ValueError('Result differs from admitted target definition.')
        if self.phase == 'verified' and self.result is None:
            raise ValueError('Verification requires observed ownership.')
        return self
