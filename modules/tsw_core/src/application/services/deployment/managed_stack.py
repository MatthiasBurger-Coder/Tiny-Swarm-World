"""One management writer; receipt alone never commits installation ownership."""
import asyncio
import time

from tiny_swarm_world.application.services.shared.settled_blocking import settled_blocking
from tiny_swarm_world.application.services.deployment import managed_stack_intent, managed_stack_write
from collections.abc import Awaitable, Callable, Mapping

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease
from tiny_swarm_world.application.ports.lifecycle.managed_stack import ManagedStackApi, ManagedStackJournal
from tiny_swarm_world.application.ports.update import PortUpdateRuntimeObserver
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.managed_stack import ManagedStackIntent
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership


class ManagedStackOperation:
    def __init__(self, api: ManagedStackApi, journal: ManagedStackJournal, observer: PortUpdateRuntimeObserver,
                 *, installation_id: str, lease: InstallationLease, attempts: int = 30, interval: float = 2.0):
        if attempts < 1 or interval < 0:
            raise ValueError('Invalid managed convergence bound.')
        self.api, self.journal, self.observer = api, journal, observer
        self.installation_id, self.lease = installation_id, lease
        self.attempts, self.interval = attempts, interval

    async def apply(self, definition: StackDefinition, environment: Mapping[str, str], images: Mapping[str, str],
                    fingerprint: str, owner: PortainerOwnership | None,
                    ownership_verified: Callable[[PortainerOwnership], Awaitable[None]], *, recovery: bool = False) -> PortainerOwnership:
        self.lease.require_active()
        endpoint = await settled_blocking(self.api.local_endpoint)
        prior = managed_stack_intent.admitted_prior(self, definition.name, endpoint, images, owner)
        owner = managed_stack_intent.recovery_owner(prior, owner, recovery)
        intent = managed_stack_intent.select_intent(self, prior, definition.name, endpoint, fingerprint, owner, recovery)
        intent, owner = await managed_stack_intent.prepare_recovery(
            self, intent, prior, definition.name, endpoint, fingerprint, owner, recovery)
        intent, identifier = await managed_stack_write.ensure_created(self, intent, definition, environment, endpoint, owner)
        observed = await settled_blocking(self.api.inspect, definition.name, endpoint, identifier)
        managed_stack_write.require_created_identity(intent, observed, owner)
        intent = await managed_stack_write.update_existing(self, intent, observed, owner, definition, fingerprint)
        # Portainer 2.45 queues asynchronous deployment; poll definition AND tasks.
        verified = await self._converge(definition.name, endpoint, identifier, fingerprint, images, observed.ownership)
        intent = self._save(intent, result=verified, phase='verified')
        await ownership_verified(verified)
        return verified

    def _save(self, intent: ManagedStackIntent, **changes) -> ManagedStackIntent:
        result = ManagedStackIntent.model_validate({**intent.model_dump(), **changes})
        self.journal.save(result)
        return result

    async def _converge(self, name, endpoint, identifier, fingerprint, images, identity):
        deadline = time.monotonic() + 300
        for attempt in range(self.attempts):
            if time.monotonic() >= deadline:
                break
            await asyncio.sleep(0 if attempt == 0 else self.interval)
            observed = (await settled_blocking(self.api.inspect, name, endpoint, identifier)).ownership
            stable = observed.model_copy(update={'definition_fingerprint': identity.definition_fingerprint}) == identity
            if not stable:
                raise LifecycleStateError('Managed ownership changed while waiting for deployment.')
            if observed.definition_fingerprint != fingerprint:
                continue
            ready = True
            for service, image in images.items():
                try:
                    task = await asyncio.wait_for(self.observer.observe(name, service), timeout=15)
                    ready = ready and task.stack_name == name and task.service_name == service and task.converged(image)
                except (OSError, RuntimeError, TimeoutError, ValueError):
                    ready = False
            if ready:
                # Rebind saved definition after task observations, not only before.
                after = (await settled_blocking(self.api.inspect, name, endpoint, identifier)).ownership
                if after == observed:
                    return after
        raise LifecycleStateError('Managed deployment did not converge; retain intent and resume the same operation.')
