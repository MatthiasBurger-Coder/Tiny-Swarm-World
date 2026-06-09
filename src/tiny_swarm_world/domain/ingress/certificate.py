from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from tiny_swarm_world.domain.ingress.desired_state import DesiredHttpsIngress
from tiny_swarm_world.domain.ingress.discovery import validate_ingress_summary_text

_REQUIRED_KEY_USAGE = frozenset({"digital_signature", "key_encipherment"})
_REQUIRED_EXTENDED_KEY_USAGE = frozenset({"server_auth"})


@dataclass(frozen=True)
class CertificateSummary:
    common_name: str
    san_dns_names: tuple[str, ...]
    issuer: str
    not_before_utc: datetime
    not_after_utc: datetime
    key_usage: tuple[str, ...]
    extended_key_usage: tuple[str, ...]
    chain_verified: bool

    def __post_init__(self) -> None:
        for field_name, value in (
            ("common_name", self.common_name),
            ("issuer", self.issuer),
        ):
            validate_ingress_summary_text(field_name, value)
            if not value:
                raise ValueError(f"{field_name} must not be empty")
        _validate_datetime("not_before_utc", self.not_before_utc)
        _validate_datetime("not_after_utc", self.not_after_utc)
        if self.not_after_utc <= self.not_before_utc:
            raise ValueError("certificate validity window is invalid")
        san_dns_names = _normalized_text_tuple("san_dns_names", self.san_dns_names)
        key_usage = _normalized_usage_tuple("key_usage", self.key_usage)
        extended_key_usage = _normalized_usage_tuple(
            "extended_key_usage", self.extended_key_usage
        )
        if not san_dns_names:
            raise ValueError("certificate summary requires at least one SAN DNS name")
        object.__setattr__(self, "san_dns_names", san_dns_names)
        object.__setattr__(self, "key_usage", key_usage)
        object.__setattr__(self, "extended_key_usage", extended_key_usage)

    def validation_for(
        self,
        desired_ingress: DesiredHttpsIngress,
        *,
        checked_at_utc: datetime | None = None,
    ) -> "CertificateValidationResult":
        checked_at = checked_at_utc or datetime.now(UTC)
        _validate_datetime("checked_at_utc", checked_at)
        missing_sans = tuple(
            hostname
            for hostname in desired_ingress.hostnames
            if hostname not in self.san_dns_names
        )
        problems: list[str] = []
        if missing_sans:
            problems.append("missing_san_dns_names")
        if checked_at < self.not_before_utc:
            problems.append("not_yet_valid")
        if checked_at >= self.not_after_utc:
            problems.append("expired")
        if not _REQUIRED_KEY_USAGE.issubset(self.key_usage):
            problems.append("key_usage_incomplete")
        if not _REQUIRED_EXTENDED_KEY_USAGE.issubset(self.extended_key_usage):
            problems.append("extended_key_usage_incomplete")
        if not self.chain_verified:
            problems.append("chain_not_verified")
        return CertificateValidationResult(
            checked_at_utc=checked_at,
            missing_san_dns_names=missing_sans,
            problems=tuple(problems),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_verified": self.chain_verified,
            "common_name": self.common_name,
            "extended_key_usage": list(self.extended_key_usage),
            "issuer": self.issuer,
            "key_usage": list(self.key_usage),
            "not_after_utc": self.not_after_utc.isoformat(),
            "not_before_utc": self.not_before_utc.isoformat(),
            "san_dns_names": list(self.san_dns_names),
        }


@dataclass(frozen=True)
class CertificateValidationResult:
    checked_at_utc: datetime
    missing_san_dns_names: tuple[str, ...] = ()
    problems: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_datetime("checked_at_utc", self.checked_at_utc)
        object.__setattr__(
            self,
            "missing_san_dns_names",
            _normalized_text_tuple("missing_san_dns_names", self.missing_san_dns_names),
        )
        object.__setattr__(
            self,
            "problems",
            _normalized_usage_tuple("problems", self.problems),
        )

    @property
    def passed(self) -> bool:
        return not self.problems

    def to_dict(self) -> dict[str, object]:
        return {
            "checked_at_utc": self.checked_at_utc.isoformat(),
            "missing_san_dns_names": list(self.missing_san_dns_names),
            "passed": self.passed,
            "problems": list(self.problems),
        }


def _validate_datetime(field_name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _normalized_text_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        validate_ingress_summary_text(field_name, value)
        if not value:
            raise ValueError(f"{field_name} values must not be empty")
        normalized.append(value)
    return tuple(dict.fromkeys(normalized))


def _normalized_usage_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(value.strip().lower() for value in values)
    if not all(value and value.replace("_", "").isalnum() for value in normalized):
        raise ValueError(f"{field_name} values must be lowercase usage identifiers")
    return tuple(dict.fromkeys(normalized))
