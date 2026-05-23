"""Stack and service deployment application service namespace.

Deployment owns stack lifecycle behavior such as ensuring that the Nexus stack
exists through compose definitions and Portainer stack APIs. The old Nexus
import path remains as a compatibility facade.
"""

from tiny_swarm_world.application.services.deployment.ensure_nexus_stack import EnsureNexusStack

__all__ = [
    "EnsureNexusStack",
]
