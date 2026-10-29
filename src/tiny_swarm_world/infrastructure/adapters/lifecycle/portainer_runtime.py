"""Async gateway lifecycle facade composed from manager, backup and API adapters."""
import asyncio
import time

import requests

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import SOURCE_VERSION
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
        raise LifecycleStateError('Portainer upgrade blocked: persisted ownership proof is unavailable.')

    async def upgrade(self, checkpoint):
        raise LifecycleStateError('Portainer upgrade blocked: persisted ownership proof is unavailable.')

    async def _recovery_stage(self, operation, *args):
        try:
            return await self._stage(operation, *args)
        except Exception:
            raise LifecycleStateError('Portainer recovery unavailable; manual reconciliation required.') from None

    async def cancel_backup(self, checkpoint):
        return await self._recovery_stage(self.backups.cancel_backup, checkpoint)

    async def restore(self, checkpoint):
        return await self._recovery_stage(self.backups.restore, checkpoint)

    async def verify(self, before, *, recovery):
        raise LifecycleStateError('Portainer update blocked: persisted ownership proof is unavailable.')

    async def inspect_recovery(self, before):
        await self._recovery_stage(self._inspect_recovery, before)



    def _inspect_recovery(self, before):
        version = SOURCE_VERSION
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
