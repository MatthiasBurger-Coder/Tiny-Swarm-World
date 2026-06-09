from __future__ import annotations

from abc import ABC, abstractmethod


class PortSonarqubeClient(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def can_authenticate(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        pass
