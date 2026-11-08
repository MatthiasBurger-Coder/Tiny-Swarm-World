from __future__ import annotations

from typing import Protocol

from tiny_swarm_world.domain.ingress.tls_contract import ResolvedTlsContract


class PortTlsContractResolver(Protocol):
    def resolve(self) -> ResolvedTlsContract:
        """Resolve and validate the installation's canonical TLS contract."""
