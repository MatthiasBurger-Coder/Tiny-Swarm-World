import asyncio

from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner


class RestApiPortCommandRunner(PortCommandRunner):
    """Legacy REST placeholder retained for compatibility; not selectable."""

    def __init__(self):
        super().__init__()
        # Use asyncio.Lock for asynchronous operations
        self.lock = asyncio.Lock()

    async def run(self, command: str) -> str:
        async with self.lock:
            self.status["current_step"] = "Unsupported command runner"
            self.status["result"] = "Unsupported"
        raise NotImplementedError(
            "REST command runner is unsupported in active Tiny Swarm World workflows."
        )
