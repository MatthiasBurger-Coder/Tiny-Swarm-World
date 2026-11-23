"""Prove an unchanged scoped Swarm deployment from a protected manager receipt."""

from shlex import quote

from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import _quote_remote_path


_RECONCILE = r'''
fingerprint() {
    local kind ids template
    for kind in service config network secret; do
        ids=$(docker "$kind" ls -q --filter "$stack_label") || return 1
        if [ -z "$ids" ]; then
            [ "$kind" != service ] || return 1
            continue
        fi
        local -a resources
        mapfile -t resources <<< "$ids"
        template='{{.ID}} {{json .Spec}}'
        if [ "$kind" = network ]; then
            template='{{.ID}} {{.Name}} {{.Driver}} {{.Scope}} {{.Internal}} {{.Attachable}} {{.Ingress}} {{.EnableIPv6}} {{json .Labels}} {{json .Options}} {{json .IPAM}}'
        fi
        docker "$kind" inspect --format "$template" "${resources[@]}" || return 1
    done
}
if [ -f "$receipt" ] && [ ! -L "$receipt" ] && [ "$(stat -c '%u:%a' -- "$receipt")" = "$EUID:600" ]; then
    if live=$(fingerprint | LC_ALL=C sort | sha256sum) &&
        printf '%s\n%s\n' "$desired" "$live" | cmp -s - "$receipt"; then
        printf '%s\n' 'Swarm stack already matches its deployment receipt.'
        exit 0
    fi
fi
rm -f -- "$receipt"
'''

_RECORD = r'''
live=$(fingerprint | LC_ALL=C sort | sha256sum)
stage=$(mktemp "${receipt}.XXXXXX")
trap 'rm -f -- "$stage"' EXIT
trap 'exit 1' HUP INT TERM
printf '%s\n%s\n' "$desired" "$live" > "$stage"
mv -T -- "$stage" "$receipt"
'''


def reconcile_script(remote_dir: str, compose_path: str, stack: str, environment: str, deploy: str) -> str:
    # Keep resolved Compose and Swarm specs, which may contain secrets, on the manager.
    return (
        'set -euo pipefail\n'
        f'receipt={_quote_remote_path(remote_dir + "/.tsw-deployment-proof")}\n'
        f'stack_label={quote("label=com.docker.stack.namespace=" + stack)}\n'
        f'compose=$({environment} docker stack config -c {_quote_remote_path(compose_path)} | sha256sum)\n'
        f"assets=$(find {_quote_remote_path(remote_dir)} -type f ! -name '.tsw-deployment-proof*' -print0"
        ' | LC_ALL=C sort -z | xargs -0 -r sha256sum -- | sha256sum)\n'
        'desired=$(printf \'%s\\n%s\\n\' "$compose" "$assets" | sha256sum)\n'
        + _RECONCILE + deploy + '\n' + _RECORD
    )
