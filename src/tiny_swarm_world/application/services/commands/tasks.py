from tiny_swarm_world.domain.command.command_entity import CommandEntity
from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner


class Task:

    def __init__(self, command_entity: CommandEntity, command_runner: PortCommandRunner):

        self.command_entity = command_entity
        self.command_runner = command_runner
