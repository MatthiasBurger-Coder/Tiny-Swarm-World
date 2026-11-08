"""Portainer-owned deployment step with the ordinary deployment workflow contract."""
from collections.abc import Callable
from typing import Any

from tiny_swarm_world.application.services.deployment.ensure_swarm_stack import EnsureSwarmStack
from tiny_swarm_world.application.services.credential_resolution import CredentialResolutionSnapshot
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class EnsureManagedStack(EnsureSwarmStack):
    def __init__(self, *args, apply_managed: Callable[..., Any], **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_managed = apply_managed

    async def run(self) -> None:
        self._applied = False
        self._consumed_credentials = None
        self.prepare_configuration()
        environment = dict(self.stack_environment)
        consumed = None
        if self.credential_snapshot is not None:
            resolved = self.credential_snapshot()
            if set(resolved.resolutions) != set(self.credential_keys):
                raise ValueError('Managed credential snapshot differs from the required keys.')
            consumed = CredentialResolutionSnapshot(resolved.resolutions)
            if any(not value.strip() for value in consumed.values.values()):
                raise ValueError('Managed credential snapshot is incomplete.')
            environment.update(consumed.values)
        await self.apply_managed(self._prepared_stack, environment)
        self._consumed_credentials = consumed
        self._applied = True

    async def verify(self) -> VerificationResult:
        return VerificationResult(target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED if self._applied else VerificationStatus.FAILED_TO_VERIFY,
            message='Managed definition, ownership and actual Swarm tasks verified.' if self._applied else 'Managed deployment has no verified result.',
            evidence={'stack_name': self.service_stack.stack_name, 'management_writer': 'portainer',
                      'task_convergence': str(self._applied).lower(), 'prune': 'false'})
