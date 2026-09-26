from __future__ import annotations

from collections.abc import Iterable, Mapping
import os
from pathlib import Path
import shlex

from tiny_swarm_world.application.ports.configuration import (
    ConfigurationSourceLoadError,
    PortConfigurationSource,
)


class ConfigurationSourceError(ConfigurationSourceLoadError):
    def __init__(self, message: str) -> None:
        super().__init__(message, safe_detail=message)


class EnvironmentConfigurationSource(PortConfigurationSource):
    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self.environment = environment

    def load(self) -> Mapping[str, str]:
        environment = self.environment if self.environment is not None else os.environ
        values: dict[str, str] = {}
        for key, value in environment.items():
            if not isinstance(key, str):
                raise ConfigurationSourceError("Configuration keys must be strings.")
            if key.startswith("TSW_"):
                if not isinstance(value, str):
                    raise ConfigurationSourceError("Configuration values must be strings.")
                values[key] = value
        return values


class ShellEnvFileConfigurationSource(PortConfigurationSource):
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Mapping[str, str]:
        if not self.path.exists():
            return {}
        values: dict[str, str] = {}
        line_numbers: dict[str, int] = {}
        try:
            content = self.path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise ConfigurationSourceError("Operator configuration could not be read.") from None
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            parsed = _parse_env_line(raw_line, line_number)
            if parsed is None:
                continue
            key, value = parsed
            if key in values:
                raise ConfigurationSourceError(
                    f"Duplicate configuration key {key} at lines {line_numbers[key]} and {line_number}."
                )
            values[key] = value
            line_numbers[key] = line_number
        return values


class CombinedConfigurationSource(PortConfigurationSource):
    def __init__(self, sources: tuple[PortConfigurationSource, ...]) -> None:
        self.sources = sources

    def load(self) -> Mapping[str, str]:
        values: dict[str, str] = {}
        for source in self.sources:
            values.update(source.load())
        return values


def _parse_env_line(raw_line: str, line_number: int) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if "$(" in line or "`" in line:
        raise ConfigurationSourceError(f"Unsupported shell syntax at line {line_number}.")
    try:
        tokens = shlex.split(line, comments=True, posix=True)
    except ValueError:
        raise ConfigurationSourceError(f"Invalid shell env syntax at line {line_number}.") from None
    if not tokens:
        return None
    if tokens[0] == "export":
        tokens = tokens[1:]
    if len(tokens) != 1 or "=" not in tokens[0]:
        raise ConfigurationSourceError(f"Unsupported shell env syntax at line {line_number}.")
    key, value = tokens[0].split("=", 1)
    if not key.startswith("TSW_"):
        return None
    if not key.replace("_", "").isalnum() or not key.isupper():
        raise ConfigurationSourceError(f"Invalid configuration key at line {line_number}.")
    return key, value


def validate_configuration_tree(value: object) -> None:
    """Reject cyclic containers and non-string keys without echoing input values."""
    active: set[int] = set()
    visited: set[int] = set()

    def visit(item: object) -> None:
        if not isinstance(item, (Mapping, list, tuple)):
            if item is not None and not isinstance(item, (str, int, float, bool)):
                raise ValueError("configuration contains an unsupported scalar type")
            return
        identity = id(item)
        if identity in active:
            raise ValueError("configuration contains recursive aliases")
        if identity in visited:
            return
        active.add(identity)
        children: Iterable[object]
        if isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                raise ValueError("configuration field names must be strings")
            children = item.values()
        else:
            children = item
        for child in children:
            visit(child)
        active.remove(identity)
        visited.add(identity)

    try:
        visit(value)
    except RecursionError:
        raise ValueError("configuration nesting is too deep") from None
