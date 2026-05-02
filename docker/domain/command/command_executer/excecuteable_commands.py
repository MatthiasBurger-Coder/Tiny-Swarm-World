from typing import Optional

from pydantic import BaseModel, Field

from application.ports.commands.port_command_runner import PortCommandRunner


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

    # Model configuration to allow arbitrary types
    model_config = {
        "arbitrary_types_allowed": True
    }
