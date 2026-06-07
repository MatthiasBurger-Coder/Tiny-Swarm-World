from __future__ import annotations

from abc import ABC, abstractmethod


class PortInfisicalClient(ABC):
    @abstractmethod
    def can_authenticate(self, email: str, password: str) -> bool:
        pass

    @abstractmethod
    def secret_item_exists(self, email: str, password: str, item_name: str) -> bool:
        pass

    @abstractmethod
    def create_secret_item(
        self,
        email: str,
        password: str,
        item_name: str,
        username: str,
        secret_value: str,
    ) -> None:
        pass
