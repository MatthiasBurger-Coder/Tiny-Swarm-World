from typing import Optional
from pydantic import BaseModel
from tiny_swarm_world.domain.network.ip_value import IpValue

class DockerIpList(BaseModel):
    external_ip: Optional[IpValue] = None
    docker_bridge_ip: Optional[IpValue] = None
    docker_overlay_ip: Optional[IpValue] = None
    gateway: Optional[IpValue] = None
