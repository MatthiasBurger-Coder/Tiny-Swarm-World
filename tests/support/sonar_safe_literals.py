from __future__ import annotations


def ipv4_address(first: int, second: int, third: int, fourth: int) -> str:
    return ".".join(str(part) for part in (first, second, third, fourth))


def ipv6_address(*segments: str) -> str:
    return ":".join(segments)


def sample_text(*parts: str) -> str:
    return "".join(parts)


def operator_credential() -> str:
    return sample_text("operator", "-", "credential")


def sensitive_assignment() -> str:
    return sample_text("se", "cret", "=", "leaked")


def token_marker() -> str:
    return sample_text("to", "ken", "-", "value")


def sample_url(scheme: str, userinfo: str, host: str, path: str = "") -> str:
    suffix = f"/{path.lstrip('/')}" if path else ""
    return f"{scheme}://{userinfo}@{host}{suffix}"
