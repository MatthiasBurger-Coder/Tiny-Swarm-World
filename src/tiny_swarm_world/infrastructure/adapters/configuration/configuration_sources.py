from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import shlex

from tiny_swarm_world.application.ports.configuration import PortConfigurationSource


class ConfigurationSourceError(ValueError):
    pass


class EnvironmentConfigurationSource(PortConfigurationSource):
    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self.environment = environment

    def load(self) -> Mapping[str, str]:
        environment = self.environment if self.environment is not None else os.environ
        return {
            str(key): str(value)
            for key, value in environment.items()
            if str(key).startswith("TSW_")
        }


class ShellEnvFileConfigurationSource(PortConfigurationSource):
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Mapping[str, str]:
        if not self.path.exists():
            return {}
        values: dict[str, str] = {}
        line_numbers: dict[str, int] = {}
        for line_number, raw_line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
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
    except ValueError as exc:
        raise ConfigurationSourceError(f"Invalid shell env syntax at line {line_number}.") from exc
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
