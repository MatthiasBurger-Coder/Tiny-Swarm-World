from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class InfisicalBootstrapState(str, Enum):
    CREATED = "created"
    ALREADY_INITIALIZED = "already_initialized"


@dataclass(frozen=True)
class InfisicalBootstrapResult:
    state: InfisicalBootstrapState
    token_returned: bool = False
    organization: str = ""
    admin_email: str = ""


class PortInfisicalBootstrapClient(ABC):
    @abstractmethod
    def bootstrap_instance(
        self,
        *,
        email: str,
        password: str,
        organization: str,
    ) -> InfisicalBootstrapResult:
        pass
