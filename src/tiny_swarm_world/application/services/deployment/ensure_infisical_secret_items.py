from __future__ import annotations

import asyncio
from dataclasses import dataclass

from tiny_swarm_world.application.ports.clients.port_infisical_client import (
    PortInfisicalClient,
)
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus


@dataclass(frozen=True)
class InfisicalSecretItem:
    item_name: str
    username: str
    secret_value: str


class EnsureInfisicalSecretItems:
    verification_target_id = "deployment:infisical-items"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        infisical_client: PortInfisicalClient,
        login_email: str,
        password: str,
        items: tuple[InfisicalSecretItem, ...],
        max_attempts: int = 12,
        wait_seconds: float = 5.0,
    ):
        if not login_email:
            raise ValueError("Infisical login email must not be empty.")
        if not password:
            raise ValueError("Infisical password must not be empty.")
        if not items:
            raise ValueError("Infisical item seed list must not be empty.")
        if max_attempts <= 0:
            raise ValueError("Infisical seed attempts must be positive.")
        if wait_seconds < 0:
            raise ValueError("Infisical seed wait seconds must not be negative.")
        self.infisical_client = infisical_client
        self.login_email = login_email
        self.password = password
        self.items = items
        self.max_attempts = max_attempts
        self.wait_seconds = wait_seconds

    async def run(self) -> None:
        for attempt in range(1, self.max_attempts + 1):
            if self.infisical_client.can_authenticate(self.login_email, self.password):
                for item in self._missing_items():
                    self.infisical_client.create_secret_item(
                        self.login_email,
                        self.password,
                        item.item_name,
                        item.username,
                        item.secret_value,
                    )
                return
            if attempt < self.max_attempts:
                await asyncio.sleep(self.wait_seconds)
        raise RuntimeError("Infisical login material could not authenticate.")

    async def verify(self) -> VerificationResult:
        await asyncio.sleep(0)
        if not self.infisical_client.can_authenticate(self.login_email, self.password):
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message="Infisical login material is not active.",
                evidence={
                    "phase": "verify",
                    "access_state": "inactive",
                    "classification": "infisical_item_inventory_missing",
                },
            )
        missing = self._missing_items()
        if missing:
            return VerificationResult(
                target_id=self.verification_target_id,
                status=VerificationStatus.FAILED_TO_VERIFY,
                message="Infisical item inventory is incomplete.",
                evidence={
                    "phase": "verify",
                    "access_state": "active",
                    "classification": "infisical_item_inventory_missing",
                    "expected_items": _item_names(self.items),
                    "missing_items": _item_names(missing),
                },
            )
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message="Infisical item inventory contains required service items.",
            evidence={
                "phase": "verify",
                "access_state": "active",
                "expected_items": _item_names(self.items),
                "missing_items": "",
            },
        )

    def _missing_items(self) -> tuple[InfisicalSecretItem, ...]:
        return tuple(
            item
            for item in self.items
            if not self.infisical_client.secret_item_exists(
                self.login_email,
                self.password,
                item.item_name,
            )
        )


def _item_names(items: tuple[InfisicalSecretItem, ...]) -> str:
    return ",".join(item.item_name for item in items)
