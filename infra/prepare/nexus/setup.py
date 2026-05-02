import argparse
import os
import sys
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[3] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from tiny_swarm_world.application.services.nexus.bootstrap_nexus import BootstrapNexus
from tiny_swarm_world.application.services.nexus.enable_nexus_anonymous_access import EnableNexusAnonymousAccess
from tiny_swarm_world.application.services.nexus.ensure_nexus_admin_access import EnsureNexusAdminAccess
from tiny_swarm_world.application.services.nexus.ensure_nexus_stack import EnsureNexusStack
from tiny_swarm_world.application.services.nexus.nexus_bootstrap_configuration import NexusBootstrapConfiguration
from tiny_swarm_world.application.services.nexus.wait_for_nexus_ready import WaitForNexusReady
from tiny_swarm_world.infrastructure.adapters.clients.docker_cli_runtime import DockerCliRuntime
from tiny_swarm_world.infrastructure.adapters.clients.nexus_http_client import NexusHttpClient
from tiny_swarm_world.infrastructure.adapters.clients.portainer_http_client import PortainerHttpClient
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml


def parse_args() -> NexusBootstrapConfiguration:
    parser = argparse.ArgumentParser(description="Bootstrap Nexus in Portainer and configure the initial admin user.")
    parser.add_argument("--portainer-url", default=os.getenv("TSW_PORTAINER_URL", "http://localhost:9000"))
    parser.add_argument("--portainer-username", default=os.getenv("TSW_PORTAINER_USERNAME", "admin"))
    parser.add_argument("--portainer-password", default=os.getenv("TSW_PORTAINER_PASSWORD", "admin1234567890"))
    parser.add_argument("--endpoint-name", default=os.getenv("TSW_PORTAINER_ENDPOINT", "local"))
    parser.add_argument("--stack-name", default=os.getenv("TSW_NEXUS_STACK_NAME", "nexus"))
    parser.add_argument("--nexus-url", default=os.getenv("TSW_NEXUS_URL", "http://localhost:8081"))
    parser.add_argument("--admin-username", default=os.getenv("TSW_NEXUS_ADMIN_USERNAME", "admin"))
    parser.add_argument("--admin-password", default=os.getenv("TSW_NEXUS_ADMIN_PASSWORD", "MyAdminPassWord1234-126354654"))
    parser.add_argument("--initial-password-path", default=os.getenv("TSW_NEXUS_INITIAL_PASSWORD_PATH", "/nexus-data/admin.password"))
    parser.add_argument("--max-attempts", type=int, default=int(os.getenv("TSW_NEXUS_MAX_ATTEMPTS", "10")))
    parser.add_argument("--wait-seconds", type=int, default=int(os.getenv("TSW_NEXUS_WAIT_SECONDS", "5")))

    args = parser.parse_args()
    return NexusBootstrapConfiguration(
        portainer_url=args.portainer_url,
        portainer_username=args.portainer_username,
        portainer_password=args.portainer_password,
        endpoint_name=args.endpoint_name,
        stack_name=args.stack_name,
        nexus_url=args.nexus_url,
        admin_username=args.admin_username,
        admin_password=args.admin_password,
        initial_password_path=args.initial_password_path,
        max_attempts=args.max_attempts,
        wait_seconds=args.wait_seconds,
    )


def main() -> None:
    configuration = parse_args()

    compose_repository = ComposeFileRepositoryYaml()
    portainer_client = PortainerHttpClient(
        configuration.portainer_url,
        configuration.portainer_username,
        configuration.portainer_password,
    )
    nexus_client = NexusHttpClient(configuration.nexus_url)
    container_runtime = DockerCliRuntime()

    bootstrapper = BootstrapNexus(
        ensure_nexus_stack=EnsureNexusStack(
            compose_repository=compose_repository,
            portainer_client=portainer_client,
            stack_name=configuration.stack_name,
            endpoint_name=configuration.endpoint_name,
        ),
        wait_for_nexus_ready=WaitForNexusReady(
            nexus_client=nexus_client,
            max_attempts=configuration.max_attempts,
            wait_seconds=configuration.wait_seconds,
        ),
        ensure_nexus_admin_access=EnsureNexusAdminAccess(
            nexus_client=nexus_client,
            container_runtime=container_runtime,
            admin_username=configuration.admin_username,
            admin_password=configuration.admin_password,
            container_name_filter=configuration.stack_name,
            initial_password_path=configuration.initial_password_path,
            max_attempts=configuration.max_attempts,
            wait_seconds=configuration.wait_seconds,
        ),
        enable_nexus_anonymous_access=EnableNexusAnonymousAccess(
            nexus_client=nexus_client,
            admin_username=configuration.admin_username,
            admin_password=configuration.admin_password,
        ),
    )
    bootstrapper.run()


if __name__ == "__main__":
    main()
