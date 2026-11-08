"""Validate received public stack assets before inode-preserving publication."""

from __future__ import annotations

import hashlib

from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    _quote_remote_path,
)


def asset_write_script(destination: str, content: str) -> str:
    """Protect live assets from truncated input; final local writes are not atomic.

    Existing Docker file bind mounts require the destination inode to survive.
    The temporary receive is verified before any destination write. A failed
    publication remains a failure and can be repaired by the same desired input.
    """
    parent = destination.rsplit("/", 1)[0]
    expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return (
        "set -eu; "
        f"mkdir -p {_quote_remote_path(parent)}; "
        f"target={_quote_remote_path(destination)}; "
        '[ ! -L "$target" ]; '
        'if [ -e "$target" ]; then [ -f "$target" ]; fi; '
        f"stage=$(mktemp {_quote_remote_path(parent + '/.tsw-asset.XXXXXX')}); "
        "trap 'rm -f -- \"$stage\"' EXIT; "
        "trap 'exit 1' HUP INT TERM; "
        'cat > "$stage"; '
        'received=$(sha256sum < "$stage"); '
        f'[ "${{received%% *}}" = "{expected}" ]; '
        'if [ -f "$target" ] && cmp -s -- "$stage" "$target"; then exit 0; fi; '
        # Do not rename over a file that a running container has bind-mounted.
        'cat "$stage" > "$target"; '
        'published=$(sha256sum < "$target"); '
        f'[ "${{published%% *}}" = "{expected}" ]'
    )
