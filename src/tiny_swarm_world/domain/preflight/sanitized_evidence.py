from __future__ import annotations

import re
from types import MappingProxyType
from typing import Mapping


UNSAFE_EVIDENCE_KEY_PARTS = (
    "command",
    "environment",
    "gateway",
    "host_ip",
    "ip_address",
    "local_path",
    "password",
    "path",
    "raw",
    "secret",
    "stderr",
    "stdout",
    "token",
    "user",
    "username",
    "vm_ip",
)

_IPV4_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_IPV6_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4}\b")
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s=:])(?:/[\w.-]+){2,}")
_WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:\\")
_COMMAND_PATTERN = re.compile(
    r"\b(?:bash|curl|docker|docker-compose|incus|iptables|lxc|netplan|netsh|python3?|sh|socat|sudo|wsl)\s+\S+",
    re.IGNORECASE,
)
_SCRIPT_PATH_PATTERN = re.compile(r"\b\S+\.(?:py|sh|ps1|bat)\b")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:api[_-]?key|passphrase|password|secret|token)\s*[:=]",
    re.IGNORECASE,
)
_URL_USERINFO_PATTERN = re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@")


def sanitized_evidence(evidence: Mapping[str, str]) -> Mapping[str, str]:
    for key, value in evidence.items():
        normalized_key = str(key).lower()
        normalized_value = str(value)
        if any(part in normalized_key for part in UNSAFE_EVIDENCE_KEY_PARTS):
            raise ValueError("evidence contains unsafe keys")
        if _contains_unsafe_evidence_value(normalized_value):
            raise ValueError("evidence contains unsafe values")
    return MappingProxyType(dict(evidence))


def _contains_unsafe_evidence_value(value: str) -> bool:
    return any(
        pattern.search(value)
        for pattern in (
            _IPV4_PATTERN,
            _IPV6_PATTERN,
            _ABSOLUTE_PATH_PATTERN,
            _WINDOWS_PATH_PATTERN,
            _COMMAND_PATTERN,
            _SCRIPT_PATH_PATTERN,
            _SECRET_ASSIGNMENT_PATTERN,
            _URL_USERINFO_PATTERN,
        )
    ) or "\n" in value or "\r" in value
