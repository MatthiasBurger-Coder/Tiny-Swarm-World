import re
from typing import Dict

from tiny_swarm_world.application.ports.commands.parameter_type import ParameterType


PARAMETER_PATTERNS = {
    ParameterType.SWARM_MANAGER_IP: re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$"),
    ParameterType.SWARM_MANAGER_PORT: re.compile(r"^\d{1,5}$"),
    ParameterType.SWARM_TOKEN: re.compile(r"^[A-Za-z0-9_.:-]+$"),
    ParameterType.VM_INSTANCE: re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"),
    ParameterType.DOCKER_BRIDGE: re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"),
}


class CommandParameterBuilder:
    """
    A builder class to replace placeholders in command templates with provided parameter values.
    Ensures that only allowed keys from the ParameterType enum are used.
    """

    @staticmethod
    def validate_params(params: Dict[ParameterType, str]) -> None:
        """
        Validates that all provided keys exist in the ParameterType Enum.

        :param params: Dictionary with Enum keys and their corresponding values
        :raises ValueError: If an invalid parameter key is found
        """
        allowed_keys = set(ParameterType)
        invalid_keys = [key for key in params if key not in allowed_keys]

        if invalid_keys:
            raise ValueError(f"Invalid parameter keys detected: {invalid_keys}")

        invalid_values = [
            key
            for key, value in params.items()
            if not PARAMETER_PATTERNS[key].fullmatch(value)
        ]
        if invalid_values:
            raise ValueError(f"Invalid command parameter values detected: {invalid_values}")

    def substitute_command(self, command_template: str, params: Dict[ParameterType, str]) -> str:
        """
        Replaces placeholders in a command with the given parameters.

        :param command_template: String containing placeholders in the format {param}
        :param params: Dictionary with Enum keys and their corresponding values
        :return: The formatted command as a string
        """
        if not params:
            return command_template
        self.validate_params(params)  # Ensure only allowed keys are used
        string_params = {
            key.value if isinstance(key, ParameterType) else key: value
            for key, value in params.items()
        }

        return command_template.format(**string_params)
