"""Strategy-based prerequisite handling for LXC Swarm stacks."""

from __future__ import annotations

import shlex
import subprocess
import base64
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.application.ports.port_tls_contract_resolver import PortTlsContractResolver
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
    def supports(self, context: StackPrerequisiteContext) -> bool:
        """Return whether this strategy owns the requested context."""

    def apply(self, context: StackPrerequisiteContext) -> None:
        """Apply the strategy after the registry has selected it."""


class ExternalOverlayNetworkStrategy:
    def supports(self, context: StackPrerequisiteContext) -> bool:
        return True

    def apply(self, context: StackPrerequisiteContext) -> None:
        for network_name in _external_overlay_network_names(context.stack_definition):
            context.ensure_external_overlay_network(network_name)


class TraefikTlsStrategy:
    def supports(self, context: StackPrerequisiteContext) -> bool:
        return context.stack_name == "traefik"

    def apply(self, context: StackPrerequisiteContext) -> None:
        context.ensure_traefik_tls_secrets()


class SonarqubeKernelStrategy:
    def supports(self, context: StackPrerequisiteContext) -> bool:
        return context.stack_name == "sonarqube"

    def apply(self, context: StackPrerequisiteContext) -> None:
        context.run_manager_shell(
            "sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null"
        )


class SwaggerAssetPrerequisiteStrategy:
    """Keep an explicit registry hook for Swagger's asset-only preparation."""

    def supports(self, context: StackPrerequisiteContext) -> bool:
        return context.stack_name == "swagger"

    def apply(self, context: StackPrerequisiteContext) -> None:
        # Swagger has no manager-side shell prerequisite; its files are
        # handled by StackAssetTransfer after this registry completes.
        return None


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
            if strategy.supports(context):
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
        tls_contract_resolver: PortTlsContractResolver,
    ) -> None:
        if external_secret_exists(cert_secret_name) and external_secret_exists(key_secret_name):
            return
        contract = tls_contract_resolver.resolve()
        certificate = base64.b64encode(contract.certificate_bytes).decode("ascii")
        private_key = base64.b64encode(contract.private_key_bytes).decode("ascii")
        script = (
            "set -e; "
            "tmpdir=$(mktemp -d); "
            "trap 'rm -rf \"$tmpdir\"' EXIT; "
            "umask 077; IFS= read -r cert; IFS= read -r key; "
            "printf '%s' \"$cert\" | base64 -d >\"$tmpdir/tls.crt\"; "
            "printf '%s' \"$key\" | base64 -d >\"$tmpdir/tls.key\"; "
            "chmod 600 \"$tmpdir/tls.crt\" \"$tmpdir/tls.key\"; "
            f"docker secret inspect -- {shlex.quote(cert_secret_name)} >/dev/null 2>&1 "
            f"|| docker secret create -- {shlex.quote(cert_secret_name)} \"$tmpdir/tls.crt\" >/dev/null; "
            f"docker secret inspect -- {shlex.quote(key_secret_name)} >/dev/null 2>&1 "
            f"|| docker secret create -- {shlex.quote(key_secret_name)} \"$tmpdir/tls.key\" >/dev/null"
        )
        run_manager_shell(script, input_text=f"{certificate}\n{private_key}\n")
