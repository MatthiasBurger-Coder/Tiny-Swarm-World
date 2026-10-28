"""Product controller composition; runtime construction remains lazy for previews."""
import logging


def build_product_upgrade(*, adoption_file=None, runtime_factory, platform_factory, deployment_factory):
    from tiny_swarm_world.application.services.product_upgrade import ProductUpgradeService
    from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_installation import PreparedProductInstallation
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal import JsonProductJournal
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_source import OfficialProductSource
    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_runtime import ClassicProductRuntime
    from tiny_swarm_world.infrastructure.process.runner import SubprocessProcessRunner

    lifecycle = build_installation_lifecycle_service()
    root = lifecycle.catalog.root
    installation = PreparedProductInstallation(root, lifecycle.manifests, lifecycle.catalog,
        OfficialProductSource(), SubprocessProcessRunner(), adoption_file=adoption_file)

    def shell_factory():
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend

        return LxcManagerShellGateway(backend=ManagedLxcBackend.INCUS, manager_node='swarm-manager',
            timeout_seconds=30, logger=logging.getLogger('ProductUpgrade'))

    def api_factory():
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import LxcPortainerHttpClient
        from tiny_swarm_world.domain.node_provider import ManagedLxcBackend

        return LxcPortainerHttpClient(backend=ManagedLxcBackend.INCUS, username='admin',
            password=runtime_factory._required_operator_secret_value('TSW_PORTAINER_ADMIN_PASSWORD'))._client()

    runtime = ClassicProductRuntime(root, shell_factory, api_factory, platform_factory, deployment_factory,
                                   configuration_verifier=installation.verify_bound_runtime)
    return ProductUpgradeService(lifecycle.manifests, installation,
        JsonProductJournal(lifecycle.manifests.path.parent / 'product-upgrade.json',
                           source_binder=installation.bind_configuration), runtime)
