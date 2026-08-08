"""Strategy-based prerequisite handling for LXC Swarm stacks."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import (
    _external_overlay_network_names,
)


ManagerShell = Callable[..., subprocess.CompletedProcess[str]]
SecretExists = Callable[[str], bool]


@dataclass(frozen=True)
class StackPrerequisiteContext:
    stack_name: str
    stack_definition: StackDefinition
    ensure_external_overlay_network: Callable[[str], None]
    ensure_traefik_tls_secrets: Callable[[], None]
    run_manager_shell: ManagerShell


class StackPrerequisiteStrategy(Protocol):
    def apply(self, context: StackPrerequisiteContext) -> None:
        """Apply this strategy when it matches the requested stack."""


class ExternalOverlayNetworkStrategy:
    def apply(self, context: StackPrerequisiteContext) -> None:
        for network_name in _external_overlay_network_names(context.stack_definition):
            context.ensure_external_overlay_network(network_name)


class TraefikTlsStrategy:
    def apply(self, context: StackPrerequisiteContext) -> None:
        if context.stack_name == "traefik":
            context.ensure_traefik_tls_secrets()


class SonarqubeKernelStrategy:
    def apply(self, context: StackPrerequisiteContext) -> None:
        if context.stack_name != "sonarqube":
            return
        context.run_manager_shell(
            "sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null"
        )


class SwaggerAssetPrerequisiteStrategy:
    """Keep an explicit registry hook for Swagger's asset-only preparation."""

    def apply(self, context: StackPrerequisiteContext) -> None:
        if context.stack_name == "swagger":
            # Swagger has no manager-side shell prerequisite; its files are
            # handled by StackAssetTransfer after this registry completes.
            return


class StackPrerequisiteRegistry:
    """Apply ordered, stack-specific prerequisite strategies."""

    def __init__(self, strategies: Sequence[StackPrerequisiteStrategy] | None = None) -> None:
        self.strategies = tuple(
            strategies
            or (
                ExternalOverlayNetworkStrategy(),
                TraefikTlsStrategy(),
                SonarqubeKernelStrategy(),
                SwaggerAssetPrerequisiteStrategy(),
            )
        )

    def ensure(
        self,
        stack_name: str,
        stack_definition: StackDefinition,
        *,
        ensure_external_overlay_network: Callable[[str], None],
        ensure_traefik_tls_secrets: Callable[[], None],
        run_manager_shell: ManagerShell,
    ) -> None:
        context = StackPrerequisiteContext(
            stack_name=stack_name,
            stack_definition=stack_definition,
            ensure_external_overlay_network=ensure_external_overlay_network,
            ensure_traefik_tls_secrets=ensure_traefik_tls_secrets,
            run_manager_shell=run_manager_shell,
        )
        for strategy in self.strategies:
            strategy.apply(context)

    def ensure_external_overlay_network(
        self,
        name: str,
        *,
        run_manager_shell: ManagerShell,
    ) -> None:
        result = run_manager_shell(
            f"docker network inspect -- {shlex.quote(name)} >/dev/null 2>&1",
            check=False,
        )
        if result.returncode == 0:
            return
        run_manager_shell(
            "docker network create --driver overlay --attachable -- "
            f"{shlex.quote(name)} >/dev/null"
        )

    def ensure_traefik_tls_secrets(
        self,
        cert_secret_name: str,
        key_secret_name: str,
        *,
        external_secret_exists: SecretExists,
        run_manager_shell: ManagerShell,
    ) -> None:
        if external_secret_exists(cert_secret_name) and external_secret_exists(key_secret_name):
            return
        script = (
            "set -e; "
            "tmpdir=$(mktemp -d); "
            "trap 'rm -rf \"$tmpdir\"' EXIT; "
            "openssl req -x509 -nodes -newkey rsa:2048 -days 365 "
            "-subj '/CN=tsw.local' "
            "-addext 'subjectAltName=DNS:tsw.local,DNS:*.tsw.local,DNS:localhost' "
            "-keyout \"$tmpdir/tls.key\" -out \"$tmpdir/tls.crt\" >/dev/null 2>&1; "
            f"docker secret inspect -- {shlex.quote(cert_secret_name)} >/dev/null 2>&1 "
            f"|| docker secret create -- {shlex.quote(cert_secret_name)} \"$tmpdir/tls.crt\" >/dev/null; "
            f"docker secret inspect -- {shlex.quote(key_secret_name)} >/dev/null 2>&1 "
            f"|| docker secret create -- {shlex.quote(key_secret_name)} \"$tmpdir/tls.key\" >/dev/null"
        )
        run_manager_shell(script)
