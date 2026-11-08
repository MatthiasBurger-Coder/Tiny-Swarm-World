"""Sanitized migration-check parsing and fixed non-admitting transport."""
from __future__ import annotations

from collections.abc import Sequence
import json
import sys

from tiny_swarm_world.application.ports.lifecycle.migration_admission import (
    MigrationAdmissionRequest, MigrationAdmissionResult, MigrationAdmissionStatus,
)
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode
from tiny_swarm_world.infrastructure.adapters.cli.migration_preview import _FLAG_OPTIONS, _VALUE_OPTIONS
from tiny_swarm_world.infrastructure.composition import build_migration_admission_service


_BLOCKED = {"status": "BLOCKED_UNKNOWN", "source": "operator_local_unverified", "applied": False, "qualified": False}
_CANDIDATE_OPTIONS = frozenset({"--version", "--exposure", "--listen-address"})
_OTHER_ACTIONS = frozenset({"migration-preview", "list", "updates", "update", "add", "remove"})


def _emit_blocked() -> None:
    print(json.dumps(_BLOCKED, separators=(",", ":"), ensure_ascii=True))
    raise SystemExit(2)


def _is_action(token: str) -> bool:
    return (token.startswith("migration-check")
            or (token.startswith("migration-") and "migration-check".startswith(token)))


def _is_attempt(argv: Sequence[str]) -> bool:
    positionals: list[str] = []
    value_options = _VALUE_OPTIONS | _CANDIDATE_OPTIONS
    all_options = value_options | _FLAG_OPTIONS
    positional_only = False
    index = 0
    while index < len(argv):
        token = argv[index]
        if not positional_only and token == "--":
            positional_only = True
        elif not positional_only and token.startswith("-") and token != "-":
            name = token.split("=", 1)[0]
            matches = [name] if name in all_options else [option for option in all_options if option.startswith(name)]
            if "=" not in token and len(matches) == 1 and matches[0] in value_options and index + 1 < len(argv):
                index += 1
        else:
            positionals.append(token)
        index += 1
    if positionals and _is_action(positionals[0]):
        return True
    for index, value in enumerate(positionals):
        if value != "services":
            continue
        for item in positionals[index + 1:]:
            if item in _OTHER_ACTIONS or item.startswith("migration-preview="):
                return False
            if _is_action(item):
                return True
    return False


def prepare_arguments(argv: Sequence[str] | None) -> tuple[list[str], MigrationAdmissionRequest | None]:
    """Separate exact action-specific options before the ordinary CLI parser."""
    raw = list(sys.argv[1:] if argv is None else argv)
    if not _is_attempt(raw):
        return raw, None
    if raw[:2] != ["services", "migration-check"]:
        _emit_blocked()
    values: dict[str, str] = {}
    index = 2
    while index < len(raw):
        token = raw[index]
        name, separator, value = token.partition("=")
        if name not in _CANDIDATE_OPTIONS or name in values:
            _emit_blocked()
        if not separator:
            index += 1
            if index >= len(raw) or raw[index].startswith("-"):
                _emit_blocked()
            value = raw[index]
        if not value:
            _emit_blocked()
        values[name] = value
        index += 1
    if set(values) != _CANDIDATE_OPTIONS:
        _emit_blocked()
    if values["--exposure"] not in {"published", "not_applicable", "internal"}:
        _emit_blocked()
    try:
        exposure = SwaggerMode(values["--exposure"])
    except ValueError:
        _emit_blocked()
        raise AssertionError("unreachable")
    listen = values["--listen-address"]
    if listen not in {"127.0.0.1", "0.0.0.0"}:
        _emit_blocked()
    request = MigrationAdmissionRequest(values["--version"], exposure, listen)
    return ["services", "migration-check"], request


def run_migration_check(request: object) -> None:
    try:
        if type(request) is not MigrationAdmissionRequest:
            _emit_blocked()
        with build_migration_admission_service() as service:
            result = service.evaluate(request)
        if (type(result) is not MigrationAdmissionResult
                or result.status not in {MigrationAdmissionStatus.BLOCKED_UNKNOWN, MigrationAdmissionStatus.BLOCKED_UNSUPPORTED}
                or result.applied is not False or result.qualified is not False):
            _emit_blocked()
        print(json.dumps({"status": result.status.value, "source": "operator_local_unverified",
                          "applied": False, "qualified": False}, separators=(",", ":"), ensure_ascii=True))
        raise SystemExit(2)
    except Exception:
        _emit_blocked()
