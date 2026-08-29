from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class TlsAuthorityMode(StrEnum):
    EXTERNAL = "external"
    MANAGED = "managed"


@dataclass(frozen=True)
class ResolvedTlsContract:
    mode: TlsAuthorityMode
    ca_certificate: Path
    leaf_certificate: Path
    leaf_private_key: Path
    trust_bundle: Path
    certificate_secret_name: str
    private_key_secret_name: str
    lifecycle_fingerprint: str
    ca_private_key: Path | None = None
    certificate_bytes: bytes = field(default=b"", repr=False)
    private_key_bytes: bytes = field(default=b"", repr=False)

    def __post_init__(self) -> None:
        for value in (
            self.ca_certificate,
            self.leaf_certificate,
            self.leaf_private_key,
            self.trust_bundle,
        ):
            if not value.is_absolute():
                raise ValueError("TLS contract paths must be absolute")
        if self.ca_private_key is not None and not self.ca_private_key.is_absolute():
            raise ValueError("TLS contract paths must be absolute")
        if not self.certificate_secret_name.strip() or not self.private_key_secret_name.strip():
            raise ValueError("TLS secret names must not be empty")
        if len(self.lifecycle_fingerprint) != 64 or not all(
            character in "0123456789abcdef" for character in self.lifecycle_fingerprint
        ):
            raise ValueError("TLS lifecycle fingerprint must be SHA-256 hexadecimal")
        if not self.certificate_bytes or not self.private_key_bytes:
            raise ValueError("TLS contract requires validated material snapshots")
