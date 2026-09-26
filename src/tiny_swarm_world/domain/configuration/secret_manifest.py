"""Parser-independent secret manifest values and invariants."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

SecretManifestType = Literal["managed_secret", "external_user_secret", "placeholder_only"]
SecretPolicy = Literal["keep_existing", "rotate"]
MANIFEST_TYPE_BY_SOURCE = {
    "internal_test_catalog": "managed_secret",
    "external_user_secret": "external_user_secret",
    "placeholder_only": "placeholder_only",
}


class SecretManifestValidationError(ValueError):
    """Safe manifest error that contains no external values or parser details."""


@dataclass(frozen=True)
class SecretManifestEntry:
    key: str
    service: str
    type: SecretManifestType
    environment: str
    description: str
    source: str
    required: bool
    policy: SecretPolicy = "keep_existing"
    owner: str = ""
    storage: str = ""
    lifecycle: str = ""

    def __post_init__(self) -> None:
        for name in ("key", "service", "type", "environment", "description", "source", "policy", "owner", "storage", "lifecycle"):
            if not isinstance(getattr(self, name), str):
                raise SecretManifestValidationError(f"Secret manifest field {name} must be a string.")
        if not re.fullmatch(r"TSW_[A-Z0-9]+(?:_[A-Z0-9]+)+", self.key):
            raise SecretManifestValidationError("Invalid TSW secret key.")
        if self.type not in {"managed_secret", "external_user_secret", "placeholder_only"}:
            raise SecretManifestValidationError("Invalid secret type.")
        if self.policy not in {"keep_existing", "rotate"}:
            raise SecretManifestValidationError("Invalid secret policy.")
        if not self.source.strip():
            raise SecretManifestValidationError("Secret manifest source must not be empty.")
        expected = MANIFEST_TYPE_BY_SOURCE.get(self.source)
        if expected is not None and self.type != expected:
            raise SecretManifestValidationError("Secret type/source mismatch.")
        if not isinstance(self.required, bool):
            raise SecretManifestValidationError("Secret manifest required must be a boolean.")
