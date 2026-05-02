"""Stack and service deployment application service namespace.

This module marks the target Deployment boundary without moving existing
services yet. `EnsureNexusStack` still lives in the Nexus package for backward
compatibility, but new code can import it from the deployment namespace.
"""

from tiny_swarm_world.application.services.nexus.ensure_nexus_stack import EnsureNexusStack

__all__ = [
    "EnsureNexusStack",
]
