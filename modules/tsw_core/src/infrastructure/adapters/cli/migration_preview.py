"""Read-only migration preview transport with a closed output shape."""
from collections.abc import Sequence
import json
import sys

from tiny_swarm_world.infrastructure.composition import build_migration_preview_service


BLOCKED = {"status": "BLOCKED_UNKNOWN", "source": "operator_local_unverified", "applied": False, "qualified": False}


_VALUE_OPTIONS = frozenset({
    "--confirm", "--service-profile", "--node-provider", "--lxc-backend", "--runtime",
    "--stack", "--service", "--from-image", "--to-image", "--services", "--to",
    "--adoption-manifest", "--selection-config",
})
_FLAG_OPTIONS = frozenset({
    "--list-workflows", "--preflight", "--live", "--approve-live", "--json",
    "--allow-wsl-windows-filesystem", "--linux-forwarding", "--incus", "--apply",
    "--preview", "--recover", "--minimal", "--help",
})


def _is_migration_preview_request(argv: Sequence[str]) -> bool:
    """Recognize positional command roles without inspecting option values."""
    positionals: list[str] = []
    positional_only = False
    index = 0
    while index < len(argv):
        token = argv[index]
        if not positional_only and token == "--":
            positional_only = True
        elif not positional_only and token.startswith("-") and token != "-":
            name = token.split("=", 1)[0]
            matches = [name] if name in _VALUE_OPTIONS | _FLAG_OPTIONS else [
                option for option in _VALUE_OPTIONS | _FLAG_OPTIONS if option.startswith(name)
            ]
            if "=" not in token and len(matches) == 1 and matches[0] in _VALUE_OPTIONS and index + 1 < len(argv):
                index += 1
        else:
            positionals.append(token)
        index += 1
    if positionals and (positionals[0] == "migration-preview"
                        or positionals[0].startswith("migration-preview=")):
        return True
    for index, token in enumerate(positionals):
        if token == "services" and any(
                item == "migration-preview" or item.startswith("migration-preview=")
                for item in positionals[index + 1:]):
            return True
    return False



def prepare_arguments(argv: Sequence[str] | None) -> list[str]:
    """Reject malformed preview invocations without exposing argument bytes."""
    raw = list(sys.argv[1:] if argv is None else argv)
    if _is_migration_preview_request(raw) and raw != ["services", "migration-preview"]:
        print(json.dumps(BLOCKED, separators=(",", ":"), ensure_ascii=True))
        raise SystemExit(2)
    return raw


def run_migration_preview() -> None:
    try:
        with build_migration_preview_service() as service:
            result = service.preview()
        print(json.dumps(result, separators=(",", ":"), ensure_ascii=True))
    except Exception:
        print(json.dumps(BLOCKED, separators=(",", ":"), ensure_ascii=True))
        raise SystemExit(2) from None
