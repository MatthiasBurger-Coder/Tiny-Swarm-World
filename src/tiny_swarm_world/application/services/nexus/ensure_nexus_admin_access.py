import asyncio
import logging
import time

from tiny_swarm_world.application.ports.clients.port_container_runtime import PortContainerRuntime
from tiny_swarm_world.application.ports.clients.port_nexus_client import PortNexusClient
from tiny_swarm_world.application.ports.ui.port_ui import AGGREGATE_INSTANCE, PortUI
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


class NexusAdminAccessRecoveryBlocked(RuntimeError):
    def __init__(self, message: str, *, diagnostic: str, operator_action: str):
        super().__init__(message)
        self.diagnostic = diagnostic
        self.operator_action = operator_action


class EnsureNexusAdminAccess:
    verification_target_id = "artifacts:nexus-admin-access"

    def __init__(
        self,
        nexus_client: PortNexusClient,
        container_runtime: PortContainerRuntime,
        admin_username: str,
        admin_password: str,
        container_name_filter: str,
        initial_password_path: str,
        max_attempts: int,
        wait_seconds: int,
        ui: PortUI | None = None,
    ):
        self.nexus_client = nexus_client
        self.container_runtime = container_runtime
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.container_name_filter = container_name_filter
        self.initial_password_path = initial_password_path
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds
        self.ui = ui
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        try:
            self._run()
        except Exception as exc:
            safe_error = _safe_exception_summary(exc)
            self.logger.error(
                "Failed to ensure Nexus admin access. Error: %s",
                safe_error,
            )
            if self.ui is not None:
                self.ui.update_status(
                    instance=AGGREGATE_INSTANCE,
                    task=self.verification_target_id,
                    step="Error",
                    result="failed_to_apply",
                )
            raise

    def _run(self) -> None:
        if self.nexus_client.can_authenticate(self.admin_username, self.admin_password):
            self.logger.info("Nexus admin credentials are already active.")
            return

        container_name = self._resolve_container_name()
        initial_password = self._read_initial_password(container_name)

        last_exception: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                self._rotate_admin_password(initial_password)
                if self._can_authenticate_with_retry(self.admin_password):
                    return
                last_exception = None
            except RuntimeError as exc:
                last_exception = exc

            if attempt < self.max_attempts:
                self.logger.info(
                    "Nexus admin access rotation is not ready yet. "
                    f"Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise NexusAdminAccessRecoveryBlocked(
            "Nexus admin password rotation completed without producing valid credentials.",
            diagnostic="rotated_credentials_inactive",
            operator_action=(
                "Check configured Nexus admin access value or reset existing "
                "Nexus state before rerunning setup."
            ),
        ) from last_exception

    def _rotate_admin_password(self, initial_password: str) -> None:
        admin_user = self.nexus_client.get_user(
            self.admin_username,
            initial_password,
            self.admin_username,
        )
        if admin_user.status != "active":
            self.logger.info("Activating Nexus admin user.")
            self.nexus_client.update_user(
                self.admin_username,
                initial_password,
                admin_user.model_copy(update={"status": "active"}),
            )

        self.logger.info("Rotating Nexus admin password.")
        self.nexus_client.change_password(
            self.admin_username,
            initial_password,
            self.admin_username,
            self.admin_password,
        )

    def _can_authenticate_with_retry(self, password: str) -> bool:
        for attempt in range(1, self.max_attempts + 1):
            if self.nexus_client.can_authenticate(self.admin_username, password):
                return True
            if attempt < self.max_attempts:
                self.logger.info(
                    "Nexus admin credentials are not active yet. "
                    f"Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)
        return False

    def _resolve_container_name(self) -> str:
        for attempt in range(1, self.max_attempts + 1):
            container_names = self.container_runtime.find_container_names(self.container_name_filter)
            if container_names:
                container_name = min(container_names)
                self.logger.info(f"Using Nexus container '{container_name}'.")
                return container_name

            if attempt < self.max_attempts:
                self.logger.info(
                    f"No Nexus container matched '{self.container_name_filter}'. "
                    f"Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise NexusAdminAccessRecoveryBlocked(
            f"No container found for filter '{self.container_name_filter}'.",
            diagnostic="nexus_container_not_found",
            operator_action="Verify the Nexus stack service is running before rerunning setup.",
        )

    def _read_initial_password(self, container_name: str) -> str:
        for attempt in range(1, self.max_attempts + 1):
            if self.container_runtime.file_exists(container_name, self.initial_password_path):
                password = self.container_runtime.read_file(container_name, self.initial_password_path).strip()
                if password:
                    self.logger.info("Read initial Nexus admin password from container.")
                    return password

            if attempt < self.max_attempts:
                self.logger.info(
                    f"Initial password file '{self.initial_password_path}' is not available yet. "
                    f"Waiting {self.wait_seconds} seconds before attempt {attempt + 1}."
                )
                time.sleep(self.wait_seconds)

        raise NexusAdminAccessRecoveryBlocked(
            f"Could not read Nexus admin password from '{self.initial_password_path}'.",
            diagnostic="initial_admin_value_unavailable",
            operator_action=(
                "Check configured Nexus admin access value or reset existing Nexus "
                "state before rerunning setup."
            ),
        )

    async def verify(self) -> VerificationResult:
        await asyncio.sleep(0)
        try:
            authenticated = self.nexus_client.can_authenticate(self.admin_username, self.admin_password)
        except Exception as exc:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message=f"Nexus admin verification failed: {exc.__class__.__name__}",
                evidence={"access_state": "unknown", "phase": "verify"},
            )
        if authenticated:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.VERIFIED,
                message="Nexus admin credentials are active.",
                evidence={"access_state": "active", "phase": "verify"},
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.FAILED_TO_VERIFY,
            message="Nexus admin credentials are not active.",
            evidence={"access_state": "inactive", "phase": "verify"},
        )


def _safe_exception_summary(exc: Exception) -> str:
    diagnostic = getattr(exc, "diagnostic", None)
    if diagnostic:
        return f"{exc.__class__.__name__}. Diagnostic: {diagnostic}."
    return f"{exc.__class__.__name__}. Diagnostic payload redacted."
