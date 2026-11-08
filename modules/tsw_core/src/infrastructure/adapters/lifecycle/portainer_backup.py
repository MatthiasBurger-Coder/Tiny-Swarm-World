"""Bounded Classic Portainer manager runtime operations."""
import re

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import SOURCE_VERSION, images

from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_topology import inspect_topology


class PortainerColdBackup:
    def __init__(self, state):
        self.state = state

    def directory(self, checkpoint):
        if re.fullmatch(r'[0-9a-f]{32}', checkpoint.operation_id) is None:
            raise LifecycleStateError('Invalid Portainer operation identity.')
        return '/var/lib/tiny-swarm-world/portainer-backups/' + checkpoint.operation_id


    def backup(self, checkpoint):
        path = self.state.volume_path(checkpoint.before.volume)
        directory = self.directory(checkpoint)
        # Establish writable storage and enough free bytes before stopping anything.
        self.state.run(f'set -eu; umask 077; mkdir -p {directory}; test ! -e {directory}/state.tar; '
                  f'needed=$(du -sk --apparent-size {path} | cut -f1); available=$(df -Pk {directory} | tail -1 | awk \'{{print $4}}\'); '
                  'test "$available" -gt "$((needed * 2 + 10240))"')
        succeeded = False
        try:
            self.state.stop()
            self.state.run(f'set -eu; umask 077; tar -cpf {directory}/state.tar -C {path} .; '
                      f'tar -tf {directory}/state.tar >/dev/null; sync {directory}/state.tar')
            digest = self.state.run(f'sha256sum {directory}/state.tar').split()[0]
            if re.fullmatch(r'[0-9a-f]{64}', digest) is None:
                raise LifecycleStateError('Backup checksum unavailable.')
            succeeded = True
            return 'sha256:' + digest
        finally:
            # Backup failures leave the unchanged source service available.
            if not succeeded:
                self.state.run('docker service scale portainer_portainer=1')


    def check_backup(self, checkpoint):
        if not checkpoint.backup_digest or re.fullmatch(r'sha256:[0-9a-f]{64}', checkpoint.backup_digest) is None:
            raise LifecycleStateError('Verified Portainer backup required before mutation.')
        directory = self.directory(checkpoint)
        checksum = self.state.run(f'sha256sum {directory}/state.tar').split()[0]
        if 'sha256:' + checksum != checkpoint.backup_digest:
            raise LifecycleStateError('Portainer backup checksum mismatch; no mutation admitted.')
        self.state.run(f'tar -tf {directory}/state.tar >/dev/null')


    def restore(self, checkpoint):
        inspect_topology(self.state, before=checkpoint.before, allow_stopped=True)
        self.check_backup(checkpoint)  # No Portainer API call on the restore path.
        path = self.state.volume_path(checkpoint.before.volume, require_database=False)
        directory = self.directory(checkpoint)
        self.state.stop()
        # Preserve failed state instead of deleting it. A new directory per retry
        # also preserves recovery interrupted after moving only some files.
        self.state.run(f'set -eu; umask 077; archive=$(mktemp -d {directory}/failed-state.XXXXXX); '
                  f'find {path} -mindepth 1 -maxdepth 1 -exec mv -t "$archive" -- {{}} +; '
                  f'tar -xpf {directory}/state.tar -C {path}')
        self.state.set_images(SOURCE_VERSION)


    def cancel_backup(self, checkpoint):
        services, _, _ = inspect_topology(self.state, before=checkpoint.before, allow_stopped=True)
        for service, component in (('portainer_portainer', 'portainer'), ('portainer_agent', 'portainer-agent')):
            actual = services[service]['Spec']['TaskTemplate']['ContainerSpec']['Image']
            if actual.split('@')[-1] != images(SOURCE_VERSION)[component].split('@')[-1]:
                raise LifecycleStateError('Source-only recovery refused: image changed without a verified backup.')
        self.state.volume_path(checkpoint.before.volume)
        self.state.run('docker service scale portainer_portainer=1')
        self.state.wait_images(SOURCE_VERSION)
