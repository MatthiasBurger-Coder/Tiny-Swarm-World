from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from tiny_swarm_world.domain.inventory import VerificationResult
from tiny_swarm_world.domain.node_provider import NodeSpec, ProviderSelection


class PortManagedNodeTeardown(ABC):
    @abstractmethod
    async def reset_nodes(
        self,
        nodes: Sequence[NodeSpec],
        selection: ProviderSelection,
    ) -> VerificationResult:
        """Reset configured managed nodes and return sanitized verification evidence.

        Implementations must keep concrete provider commands, raw output, and
        host-specific details inside the infrastructure adapter. If a blocked
        result is returned after mutation started, evidence should include
        ``applied=true``.
        """
        pass

    @abstractmethod
    async def destroy_nodes(
        self,
        nodes: Sequence[NodeSpec],
        selection: ProviderSelection,
    ) -> VerificationResult:
        """Destroy configured managed nodes and return sanitized verification evidence.

        Implementations must prove the requested nodes reached terminal state
        without exposing concrete LXC/Docker commands or raw command output. If
        a blocked result is returned after mutation started, evidence should
        include ``applied=true``.
        """
        pass
