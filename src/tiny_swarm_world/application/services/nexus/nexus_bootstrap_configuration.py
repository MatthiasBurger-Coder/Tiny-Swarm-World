from dataclasses import dataclass


@dataclass(frozen=True)
class NexusBootstrapConfiguration:
    portainer_url: str = "http://localhost:9000"
    portainer_username: str = "admin"
    portainer_password: str = ""
    endpoint_name: str = "local"
    stack_name: str = "nexus"
    nexus_url: str = "http://localhost:8081"
    admin_username: str = "admin"
    admin_password: str = ""
    initial_password_path: str = "/nexus-data/admin.password"
    max_attempts: int = 10
    wait_seconds: int = 5
    anonymous_access_enabled: bool = False
