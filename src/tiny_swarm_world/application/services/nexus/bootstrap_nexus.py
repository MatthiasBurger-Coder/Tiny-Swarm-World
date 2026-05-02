from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class BootstrapNexus:
    def __init__(
        self,
        ensure_nexus_stack,
        wait_for_nexus_ready,
        ensure_nexus_admin_access,
        enable_nexus_anonymous_access,
    ):
        self.ensure_nexus_stack = ensure_nexus_stack
        self.wait_for_nexus_ready = wait_for_nexus_ready
        self.ensure_nexus_admin_access = ensure_nexus_admin_access
        self.enable_nexus_anonymous_access = enable_nexus_anonymous_access
        self.logger = LoggerFactory.get_logger(self.__class__)

    def run(self) -> None:
        self.logger.info("Starting Nexus bootstrap.")
        self.ensure_nexus_stack.run()
        self.wait_for_nexus_ready.run()
        self.ensure_nexus_admin_access.run()
        self.enable_nexus_anonymous_access.run()
        self.logger.info("Nexus bootstrap finished.")
