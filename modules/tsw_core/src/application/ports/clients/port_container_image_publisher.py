from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure
from abc import ABC, abstractmethod

from tiny_swarm_world.domain.artifacts import ContainerImageContract


class PortContainerImagePublisher(ABC):
    @abstractmethod
    def publish_image(self, contract: ContainerImageContract) -> None:
        pass

    @abstractmethod
    def image_available(self, contract: ContainerImageContract) -> bool:
        pass


class PublicImagePullRejected(OperationError, RuntimeError):
    def __init__(self, image_ref: str, *, diagnostic: str, operator_action: str) -> None:
        super().__init__(OperationFailure.for_cause(
            "image.pull", "image_publisher",
            "registry_rate_limited" if diagnostic == "registry_rate_limited" else "process_exit_failed",
        ))
        self.args = (f"Public container image pull failed. {self.args[0]}",)
        self.image_ref = image_ref
        self.diagnostic = diagnostic
        self.operator_action = operator_action


class ImagePublisherOperationRejected(OperationError, RuntimeError):
    def __init__(
        self,
        *,
        operation: str,
        diagnostic: str,
        operator_action: str,
        exit_code: int | None = None,
        failure: OperationFailure | None = None,
    ) -> None:
        cause = {
            "operation_timeout": "process_timeout",
            "operation_unavailable": "launch_os_error",
            "registry_rate_limited": "registry_rate_limited",
            "registry_unreachable": "dependency_unavailable",
            "network_unreachable": "dependency_unavailable",
            "manager_storage_exhausted": "filesystem_error",
        }.get(diagnostic, "process_exit_failed")
        super().__init__(failure or OperationFailure.for_cause("image.publish", "image_publisher", cause))
        self.operation = operation
        self.diagnostic = diagnostic
        self.operator_action = operator_action
        if exit_code is not None and type(exit_code) is not int:
            raise TypeError("Process exit code must be numeric.")
        self.exit_code = exit_code
        if exit_code is not None:
            self.args = (f"{self.args[0]} Exit code: {exit_code}.",)



class ImagePublisherError(OperationError, RuntimeError):
    """Expected image transport failure."""

    def __init__(self, failure, *, exit_code: int | None = None):
        super().__init__(failure)
        if exit_code is not None and type(exit_code) is not int:
            raise TypeError("Process exit code must be numeric.")
        detail = "Public container image pull failed." if failure.operation == "image.pull" else "Container image operation failed."
        if failure.operation == "image.transfer" and failure.cause == "process_timeout":
            detail = "LXC manager image transfer timed out."
        if exit_code is not None:
            detail += f" Process failed with exit code {exit_code}."
        self.args = (f"{detail} {self.args[0]}",)
