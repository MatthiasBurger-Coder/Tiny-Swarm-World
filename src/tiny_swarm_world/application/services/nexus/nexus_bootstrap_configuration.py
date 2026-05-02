from dataclasses import dataclass


@dataclass(frozen=True)
class NexusBootstrapConfiguration:
    portainer_url: str = "http://localhost:9000"
    portainer_username: str = "admin"
    portainer_password: str = "admin1234567890"
    endpoint_name: str = "local"
    stack_name: str = "nexus"
    nexus_url: str = "http://localhost:8081"
    admin_username: str = "admin"
    admin_password: str = "MyAdminPassWord1234-126354654"
    initial_password_path: str = "/nexus-data/admin.password"
    max_attempts: int = 10
    wait_seconds: int = 5
