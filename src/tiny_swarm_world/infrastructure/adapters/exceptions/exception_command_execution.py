REDACTED_VALUE = "<redacted>"


class CommandExecutionError(Exception):
    """
    Custom exception for command execution errors.
    """

    def __init__(self, command: str, return_code: int, stdout: str, stderr: str):
        """
        Constructor for the CommandExecutionError class.

        Args:
            command (str): The command that was executed.
            return_code (int): The exit code of the command.
            stdout (str): The standard output of the command.
            stderr (str): The standard error output of the command.
        """
        super().__init__(
            f"Command failed with return code {return_code}. Diagnostic payload redacted."
        )
        self.command = REDACTED_VALUE
        self.returnCode = return_code
        self.stdout = REDACTED_VALUE if stdout else ""
        self.stderr = REDACTED_VALUE if stderr else ""

    def __str__(self):
        """
        Overrides the __str__() method to provide a meaningful string representation.
        """
        return (
            f"CommandExecutionError: command failed with return code {self.returnCode}. "
            "Diagnostic payload redacted."
        )
