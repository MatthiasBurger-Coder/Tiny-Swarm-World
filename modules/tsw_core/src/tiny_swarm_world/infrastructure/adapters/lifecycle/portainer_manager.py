"""Bounded Classic Portainer manager runtime operations."""
import json
import re
import shlex

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import images


class PortainerManagerState:
    def __init__(self, shell, *, timeout_seconds=300):
        self.shell, self.timeout_seconds = shell, timeout_seconds

    def run(self, script):
        result = self.shell.run_manager_shell(script, check=False, timeout_seconds=self.timeout_seconds)
        if result.returncode != 0:
            raise LifecycleStateError('Portainer runtime stage failed; preserve checkpoint and backup, then inspect/recover.')
        return result.stdout.strip()


    def json(self, script):
        return json.loads(self.run(script))


    def services(self):
        payload = self.json('docker service inspect portainer_portainer portainer_agent')
        if not isinstance(payload, list) or len(payload) != 2:
            raise LifecycleStateError('Expected Classic Portainer server and agent services.')
        return {item['Spec']['Name']: item for item in payload}


    def volume_path(self, volume, *, require_database=True):
        if re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}', volume) is None:
            raise LifecycleStateError('Invalid Portainer volume identity.')
        info = self.json(f'docker volume inspect {shlex.quote(volume)}')[0]
        path = info['Mountpoint']
        if info['Driver'] != 'local' or info.get('Options') or path != f'/var/lib/docker/volumes/{volume}/_data':
            raise LifecycleStateError('Only default local Docker volumes on the manager are supported.')
        self.run(f'test -d {shlex.quote(path)} && test -w {shlex.quote(path)}')
        if require_database:
            self.run(f'test -s {shlex.quote(path + "/portainer.db")}')
        return path


    def stop(self):
        self.run('docker service scale portainer_portainer=0')
        self.run("timeout 60 sh -c 'while :; do tasks=$(docker ps -q --filter label=com.docker.swarm.service.name=portainer_portainer) || exit 1; test -z \"$tasks\" && exit 0; sleep 1; done'")


    def set_images(self, version):
        for component, service in (('portainer-agent', 'portainer_agent'), ('portainer', 'portainer_portainer')):
            self.run(f'docker service update --detach=true --no-resolve-image --image {images(version)[component]} {service}')
        self.run('docker service scale portainer_portainer=1')
        self.wait_images(version)


    def wait_images(self, version):
        for component, service in (('portainer', 'portainer_portainer'), ('portainer-agent', 'portainer_agent')):
            digest = images(version)[component].split('@')[1]
            # Desired-image identity alone is insufficient: every running task must
            # carry the new digest and the scheduler must report full convergence.
            self.run("set -eu; timeout 120 sh -c " + shlex.quote(
                f"while :; do replicas=$(docker service ls --filter name={service} --format '{{{{.Replicas}}}}'); "
                "case $replicas in */*) ready=${replicas%/*}; wanted=${replicas#*/};; *) exit 1;; esac; "
                f"tasks=$(docker service ps --no-trunc --filter desired-state=running --format '{{{{.Image}}}}|{{{{.CurrentState}}}}' {service}) || exit 1; "
                'if test "$ready" = "$wanted" && test "$wanted" -gt 0 && test -n "$tasks" '
                f"&& ! printf '%s\\n' \"$tasks\" | grep -v '{digest}|Running '; then exit 0; fi; sleep 2; done"))


    def wait_stack(self, stack):
        self.run("set -eu; timeout 120 sh -c " + shlex.quote(
            f"while :; do states=$(docker stack services {shlex.quote(stack)} --format '{{{{.Replicas}}}}') || exit 1; "
            'test -n "$states" || exit 1; failed=0; for state in $states; do '
            'test "${state%/*}" = "${state#*/}" && test "${state#*/}" -gt 0 || failed=1; done; '
            'test "$failed" = 0 && exit 0; sleep 2; done'))
