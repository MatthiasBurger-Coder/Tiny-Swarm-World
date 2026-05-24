import logging


class BootstrapNexus:
    def __init__(
        self,
        ensure_nexus_stack,
        wait_for_nexus_ready,
        ensure_nexus_admin_access,
        enable_nexus_anonymous_access,
        enable_anonymous_access: bool = False,
    ):
        self.ensure_nexus_stack = ensure_nexus_stack
        self.wait_for_nexus_ready = wait_for_nexus_ready
        self.ensure_nexus_admin_access = ensure_nexus_admin_access
        self.enable_nexus_anonymous_access = enable_nexus_anonymous_access
        self.enable_anonymous_access = enable_anonymous_access
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        self.logger.info("Starting Nexus bootstrap.")
        self.ensure_nexus_stack.run()
        self.wait_for_nexus_ready.run()
        self.ensure_nexus_admin_access.run()
        if self.enable_anonymous_access:
            self.enable_nexus_anonymous_access.run()
        self.logger.info("Nexus bootstrap finished.")
