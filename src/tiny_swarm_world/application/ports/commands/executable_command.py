from typing import Optional

from pydantic import BaseModel, Field

from tiny_swarm_world.application.ports.commands.port_command_runner import PortCommandRunner
from tiny_swarm_world.domain.command.command_entity import (
    CommandEvidencePolicy,
    CommandSafetyClass,
    CommandVerifySpec,
)


class ExecutableCommandEntity(BaseModel):
    """
    :param index: order of execution (1, 2, 3, ...)
    :param vm_instance_name: VM instance name
    :param description: Description of the command
    :param command: The actual executable command
    :param runner: CommandRunner type (async, multipass, ...)
    """

    index: Optional[int] = Field(default=None)
    vm_instance_name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    command: Optional[str] = Field(default=None)
    runner: Optional[PortCommandRunner] = Field(default=None)
    command_id: Optional[str] = Field(default=None)
    safety_class: Optional[CommandSafetyClass] = Field(default=None)
    verify: Optional[CommandVerifySpec] = Field(default=None)
    evidence_policy: Optional[CommandEvidencePolicy] = Field(default=None)

    model_config = {
        "arbitrary_types_allowed": True,
    }

    @property
    def mutating(self) -> bool:
        return self.safety_class is not None and self.safety_class != CommandSafetyClass.SAFE_READ
