"""Async gateway lifecycle facade composed from manager, backup and API adapters."""
import asyncio
import time

import requests

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import SOURCE_VERSION, TARGET_VERSION
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_api import PortainerUpgradeApi
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_backup import PortainerColdBackup
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_inspection import PortainerInspection
from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_manager import PortainerManagerState


class ClassicPortainerUpgradeRuntime:
    def __init__(self, shell, client, *, managed_stacks, timeout_seconds=300):
        self.api = PortainerUpgradeApi(client, managed_stacks=managed_stacks)
        self.state = PortainerManagerState(shell, timeout_seconds=timeout_seconds)
        self.backups = PortainerColdBackup(self.state)
        self.inspection = PortainerInspection(self.state, self.api)

    async def _stage(self, operation, *args):
        try:
            return await asyncio.to_thread(operation, *args)
        except LifecycleStateError:
            raise
        except (OperationError, OSError, ValueError, KeyError, TypeError, IndexError, requests.RequestException):
            raise LifecycleStateError('Portainer stage unavailable or invalid; retain checkpoint/backup and inspect recovery.') from None


    async def inspect(self):
        return await self._stage(self.inspection.inspect)

    async def backup(self, checkpoint):
        return await self._stage(self.backups.backup, checkpoint)

    async def upgrade(self, checkpoint):
        return await self._stage(self._upgrade, checkpoint)

    async def cancel_backup(self, checkpoint):
        return await self._stage(self.backups.cancel_backup, checkpoint)

    async def restore(self, checkpoint):
        return await self._stage(self.backups.restore, checkpoint)

    def _upgrade(self, checkpoint):
        self.backups.check_backup(checkpoint)
        self.state.set_images(TARGET_VERSION)


    async def verify(self, before, *, recovery):
        await self._stage(self._verify, before, recovery)


    def _verify(self, before, recovery):
        version = SOURCE_VERSION if recovery else TARGET_VERSION
        self.state.wait_images(version)
        for attempt in range(30):
            try:
                current = self.inspection.inspect(prepare_upgrade=False)
                break
            except (requests.RequestException, OperationError):
                if attempt == 29:
                    raise
                time.sleep(2)
        if (current.version != version or current.volume != before.volume
                or current.endpoints != before.endpoints or current.ownership != before.ownership
                or (current.server_id, current.agent_id, current.swarm_id) != (before.server_id, before.agent_id, before.swarm_id)):
            raise LifecycleStateError('Portainer version, access, endpoints or stack ownership changed; recovery required.')
        stack = self.api.prove_update()
        # Verify the managed update through Swarm readiness,
        # rather than treating the PUT response as deployment proof.
        self.state.wait_stack(stack)
        after = self.api.inventory()
        if after != (current.version, before.endpoints, before.ownership):
            raise LifecycleStateError('Gateway proof changed endpoint or stack ownership.')
