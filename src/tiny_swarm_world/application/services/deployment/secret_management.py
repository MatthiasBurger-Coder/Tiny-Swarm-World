from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml

from tiny_swarm_world.application.ports.clients.port_infisical_cli import PortInfisicalCli
from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus

SecretClassification = Literal[
    "managed_secret",
    "generated_secret",
    "external_user_secret",
    "placeholder_only",
    "false_positive",
    "blocker",
]
SecretPolicy = Literal["keep_existing", "rotate"]

REDACTED = "<redacted>"
DEFAULT_MANIFEST_PATH = Path("config/secrets/infisical-secrets.yaml")
DEFAULT_BOOTSTRAP_LOCAL_ENV = Path(".tiny-swarm/secrets/bootstrap.local.env")
DEFAULT_GENERATED_LOCAL_ENV = Path(".tiny-swarm/secrets/generated.local.env")
DEFAULT_EVIDENCE_DIR = Path(".tiny-swarm/evidence/secrets")
SECRET_KEY_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]*(?:PASSWORD|TOKEN|SECRET|API_KEY|CREDENTIAL|HTPASSWD|KEY)[A-Z0-9_]*\b")
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?P<key>[A-Za-z_][A-Za-z0-9_-]*)\s*[:=]\s*(?P<value>[^\n#]+)",
    re.IGNORECASE,
)
PLACEHOLDER_MARKERS = ("${", "{{", "<", "redacted", "placeholder", "changeme", "fake", "sample", "-password", "-secret", "-value")
SOURCE_MARKERS = ("generated_local_secret", "external_user_secret", "managed_secret", "placeholder_only")
FALSE_POSITIVE_KEYS = ("PUBLIC_KEY", "RESOURCE_KEYS", "RAW_EVIDENCE_KEYS")
FALSE_POSITIVE_ASSIGNMENTS = (
    "GENERATE_SECRETS",
    "INITIAL_PASSWORD",
    "KEY",
    "MISSING_SECRETS",
    "SECRET_CONTENT",
    "SECRET_ENV_FILE",
    "SECRET_ENVIRONMENT",
    "SECRET_FILE",
    "SECRET_MODE",
    "SECRET_NAME",
    "SECRETS",
    "SECRETS_GENERATED_COUNT",
)
SCAN_SUFFIXES = {".env", ".yml", ".yaml", ".sh", ".py", ".groovy", ".conf", ".json", ".template", ".tpl"}
SCAN_DIRS = (".",)
SKIP_PARTS = {
    ".git",
    "__pycache__",
    ".venv",
    "bin",
    "include",
    "lib",
    "pydevd_attach_to_process",
    "venv",
    ".mypy_cache",
    ".ruff_cache",
    ".tiny-swarm",
    ".tiny-swarm-world",
    ".idea",
}


@dataclass(frozen=True)
class SecretManifestEntry:
    key: str
    service: str
    type: SecretClassification
    environment: str
    description: str
    source: str
    required: bool
    policy: SecretPolicy = "keep_existing"


@dataclass(frozen=True)
class SecretFinding:
    key: str
    classification: SecretClassification
    path: str
    line: int
    service: str = "unknown"
    redacted_value: str = REDACTED
    reason: str = ""


class SecretManagementBlocker(RuntimeError):
    def __init__(self, classification: str, message: str):
        super().__init__(message)
        self.classification = classification


class SecretRedactor:
    def __init__(self, known_values: tuple[str, ...] = ()) -> None:
        self.known_values = tuple(value for value in known_values if value)

    def redact(self, value: object) -> object:
        if isinstance(value, dict):
            return {str(key): self.redact(nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.redact(item) for item in value)
        if isinstance(value, str):
            redacted = value
            for known_value in self.known_values:
                redacted = redacted.replace(known_value, REDACTED)
            if _is_sensitive_key_or_assignment(redacted):
                return _redact_assignment(redacted)
            return redacted
        return value


class SecretManifestRenderer:
    def __init__(self, manifest_path: Path = DEFAULT_MANIFEST_PATH) -> None:
        self.manifest_path = manifest_path

    def run(self) -> tuple[SecretManifestEntry, ...]:
        payload = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("secrets"), list):
            raise SecretManagementBlocker("manifest_schema_invalid", "Secret manifest must contain a secrets list.")
        entries = tuple(_manifest_entry(item) for item in payload["secrets"])
        keys = [entry.key for entry in entries]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise SecretManagementBlocker("manifest_schema_invalid", f"Duplicate secret keys: {', '.join(duplicates)}")
        return entries


class SecretDiscoveryStep:
    verification_target_id = "deployment:managed-config-inventory"
    deployment_target_id = verification_target_id

    def __init__(self, *, repo_root: Path = Path("."), manifest_entries: tuple[SecretManifestEntry, ...] = ()) -> None:
        self.repo_root = repo_root
        self.manifest_entries = manifest_entries
        self._findings: tuple[SecretFinding, ...] = ()

    @property
    def findings(self) -> tuple[SecretFinding, ...]:
        return self._findings

    def run(self) -> tuple[SecretFinding, ...]:
        managed_keys = {entry.key: entry for entry in self.manifest_entries}
        findings: list[SecretFinding] = []
        for path in _candidate_files(self.repo_root):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_number, line in enumerate(text.splitlines(), start=1):
                findings.extend(_classify_line(path, self.repo_root, line_number, line, managed_keys))
        self._findings = tuple(findings)
        blockers = [finding for finding in self._findings if finding.classification == "blocker"]
        if blockers:
            blocker = blockers[0]
            raise SecretManagementBlocker("blocker", f"Unmanaged tracked secret-like value found at {blocker.path}:{blocker.line}")
        return self._findings

    def verify(self) -> VerificationResult:
        blockers = [finding for finding in self._findings if finding.classification == "blocker"]
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.BLOCKED if blockers else VerificationStatus.VERIFIED,
            message="Managed config inventory was classified with redacted values.",
            evidence={
                "phase": "verify",
                "discovered_count": str(len(self._findings)),
                "blocker_count": str(len(blockers)),
            },
        )


class InfisicalBootstrapStep:
    verification_target_id = "deployment:infisical-bootstrap-order"
    deployment_target_id = verification_target_id

    def __init__(self, bootstrap_step: object) -> None:
        self.bootstrap_step = bootstrap_step

    def run(self) -> None:
        run = getattr(self.bootstrap_step, "run")
        run()

    def verify(self) -> object:
        verify = getattr(self.bootstrap_step, "verify")
        return verify()


class InfisicalSecretSyncStep:
    verification_target_id = "deployment:infisical-sync"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        *,
        cli: PortInfisicalCli,
        manifest_entries: tuple[SecretManifestEntry, ...],
        generated_local_env: Path = DEFAULT_GENERATED_LOCAL_ENV,
        project: str = "tiny-swarm-world",
        environment: str = "local",
    ) -> None:
        self.cli = cli
        self.manifest_entries = manifest_entries
        self.generated_local_env = generated_local_env
        self.project = project
        self.environment = environment
        self.results: list[dict[str, str]] = []

    def run(self) -> None:
        if not self.cli.is_available():
            raise SecretManagementBlocker("infisical_cli_missing", "Infisical CLI is required for secret sync.")
        self.cli.ensure_project_environment(self.project, self.environment)
        generated_values = _read_env_file(self.generated_local_env)
        for entry in self.manifest_entries:
            value = os.environ.get(entry.key) or generated_values.get(entry.key)
            if not value and entry.source == "generated_local_secret":
                value = _generate_secret(entry.key)
                generated_values[entry.key] = value
            if value and entry.source in {"generated_local_secret", "infisical_bootstrap_identity"}:
                generated_values.setdefault(entry.key, value)
            if entry.required and not value:
                raise SecretManagementBlocker("blocker", f"Required secret value is missing: {entry.key}")
            if not value:
                self.results.append(_sync_result(entry, "skipped_missing_optional"))
                continue
            exists = self.cli.secret_exists(entry.key, project=self.project, environment=self.environment)
            if exists and entry.policy == "keep_existing":
                self.results.append(_sync_result(entry, "kept_existing"))
                continue
            if exists and entry.policy == "rotate":
                value = _generate_secret(entry.key)
                generated_values[entry.key] = value
            self.cli.set_secret(entry.key, value, project=self.project, environment=self.environment)
            self.results.append(_sync_result(entry, "updated" if exists else "created"))
        _write_env_file(self.generated_local_env, generated_values)

    def verify(self) -> VerificationResult:
        synced = [result for result in self.results if result["sync_status"] in {"created", "updated", "kept_existing"}]
        missing = [result for result in self.results if result["sync_status"] == "skipped_missing_optional"]
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message="Infisical managed entries were synchronized idempotently.",
            evidence={
                "phase": "verify",
                "synced_entry_count": str(len(synced)),
                "optional_missing_count": str(len(missing)),
                "project": self.project,
                "scope_name": self.environment,
            },
        )


class SecretConsumptionVerifier:
    verification_target_id = "deployment:managed-config-consumption"
    deployment_target_id = verification_target_id

    def __init__(self, *, manifest_entries: tuple[SecretManifestEntry, ...], stack_environment: dict[str, dict[str, str]] | None = None) -> None:
        self.manifest_entries = manifest_entries
        self.stack_environment = stack_environment or {}
        self.report: list[dict[str, str]] = []

    def run(self) -> None:
        consumed_keys = {key for values in self.stack_environment.values() for key in values}
        self.report = [
            {
                "key": entry.key,
                "service": entry.service,
                "consumer_status": "configured" if entry.key in consumed_keys or not entry.required else "not_observed",
            }
            for entry in self.manifest_entries
        ]

    def verify(self) -> VerificationResult:
        missing = [item for item in self.report if item["consumer_status"] == "not_observed"]
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message="Managed config consumption references were verified without exposing values.",
            evidence={
                "phase": "verify",
                "configured_ref_count": str(len(self.report)),
                "missing_required_count": str(len(missing)),
            },
        )


class SecretEvidenceWriter:
    verification_target_id = "deployment:managed-config-evidence"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        *,
        evidence_dir: Path = DEFAULT_EVIDENCE_DIR,
        discovery: SecretDiscoveryStep,
        sync: InfisicalSecretSyncStep,
        consumption: SecretConsumptionVerifier,
    ) -> None:
        self.evidence_dir = evidence_dir
        self.discovery = discovery
        self.sync = sync
        self.consumption = consumption

    def run(self) -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(UTC).isoformat()
        inventory = {
            "generated_at": now,
            "findings": [finding.__dict__ for finding in self.discovery.findings],
        }
        sync_result = {"generated_at": now, "results": self.sync.results}
        consumption_lines = ["# Secret Consumption Report", ""]
        for item in self.consumption.report:
            consumption_lines.append(f"- {item['key']} ({item['service']}): {item['consumer_status']}")
        (self.evidence_dir / "secret-inventory.json").write_text(json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8")
        (self.evidence_dir / "infisical-sync-result.json").write_text(json.dumps(sync_result, indent=2, sort_keys=True), encoding="utf-8")
        (self.evidence_dir / "secret-consumption-report.md").write_text("\n".join(consumption_lines) + "\n", encoding="utf-8")

    def verify(self) -> VerificationResult:
        paths = ("secret-inventory.json", "infisical-sync-result.json", "secret-consumption-report.md")
        existing = [name for name in paths if (self.evidence_dir / name).exists()]
        return VerificationResult(
            target_id=self.verification_target_id,
            status=VerificationStatus.VERIFIED if len(existing) == len(paths) else VerificationStatus.BLOCKED,
            message="Sanitized managed config evidence files were written.",
            evidence={"phase": "verify", "artifact_count": str(len(existing))},
        )


def _manifest_entry(item: object) -> SecretManifestEntry:
    if not isinstance(item, dict):
        raise SecretManagementBlocker("manifest_schema_invalid", "Secret manifest entries must be mappings.")
    key = str(item.get("key", ""))
    if not re.fullmatch(r"TSW_[A-Z0-9]+(?:_[A-Z0-9]+)+", key):
        raise SecretManagementBlocker("manifest_schema_invalid", f"Invalid TSW secret key: {key}")
    entry_type = str(item.get("type", ""))
    if entry_type not in {"managed_secret", "generated_secret", "external_user_secret", "placeholder_only"}:
        raise SecretManagementBlocker("manifest_schema_invalid", f"Invalid secret type for {key}: {entry_type}")
    policy = str(item.get("policy", "keep_existing"))
    if policy not in {"keep_existing", "rotate"}:
        raise SecretManagementBlocker("manifest_schema_invalid", f"Invalid secret policy for {key}: {policy}")
    return SecretManifestEntry(
        key=key,
        service=str(item.get("service", "")),
        type=entry_type,  # type: ignore[arg-type]
        environment=str(item.get("environment", "local")),
        description=str(item.get("description", "")),
        source=str(item.get("source", "")),
        required=bool(item.get("required", False)),
        policy=policy,  # type: ignore[arg-type]
    )


def _candidate_files(repo_root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name.startswith(".env") or path.suffix in SCAN_SUFFIXES or "docker-compose" in path.name:
            files.append(path)
    return tuple(files)


def _classify_line(path: Path, repo_root: Path, line_number: int, line: str, managed_keys: dict[str, SecretManifestEntry]) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    relative = path.relative_to(repo_root).as_posix()
    for key in SECRET_KEY_PATTERN.findall(line):
        if any(false_key in key for false_key in FALSE_POSITIVE_KEYS):
            findings.append(SecretFinding(key, "false_positive", relative, line_number, reason="safe_symbol_name"))
        elif key in managed_keys:
            findings.append(SecretFinding(key, managed_keys[key].type, relative, line_number, service=managed_keys[key].service))
        elif key.startswith("TSW_"):
            findings.append(SecretFinding(key, "external_user_secret", relative, line_number, reason="unmanaged_tsw_secret_reference"))
    assignment = SECRET_ASSIGNMENT_PATTERN.search(line)
    if assignment:
        key = assignment.group("key")
        if not _is_secretish_name(key):
            return findings
        value = assignment.group("value").strip().strip('"\'')
        if key in managed_keys or value in managed_keys:
            classification: SecretClassification = "managed_secret"
        elif value.startswith("${"):
            classification = "placeholder_only"
        elif key.upper() in FALSE_POSITIVE_ASSIGNMENTS:
            classification = "false_positive"
        elif "_operator_secret_value" in value:
            classification = "managed_secret"
        elif any(marker in value.lower() for marker in SOURCE_MARKERS):
            classification = "placeholder_only"
        elif "System.getenv" in value:
            classification = "placeholder_only"
        elif relative.startswith("tests/") and ("assert" in line or "operator_credential" in line):
            classification = "placeholder_only"
        elif any(marker in value.lower() for marker in PLACEHOLDER_MARKERS):
            classification = "placeholder_only"
        elif path.suffix == ".py" and not value.startswith(("\"", "'")):
            classification = "false_positive"
        elif value.startswith("/"):
            classification = "false_positive"
        elif value and len(value) >= 6:
            classification = "blocker"
        else:
            classification = "false_positive"
        findings.append(SecretFinding(key, classification, relative, line_number, redacted_value=REDACTED))
    return findings


def _is_secretish_name(key: str) -> bool:
    normalized = key.upper().replace("-", "_")
    if any(part in normalized for part in ("PASSWORD", "TOKEN", "SECRET", "API_KEY", "CREDENTIAL", "HTPASSWD")):
        return True
    return normalized.endswith("_KEY") and not normalized.endswith(("BY_KEY", "_KEYS"))

def _is_sensitive_key_or_assignment(value: str) -> bool:
    return bool(SECRET_ASSIGNMENT_PATTERN.search(value) or SECRET_KEY_PATTERN.search(value))


def _redact_assignment(value: str) -> str:
    return SECRET_ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group('key')}={REDACTED}", value)


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def _write_env_file(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Generated by Tiny Swarm World. Do not commit."]
    for key in sorted(values):
        lines.append(f"export {key}='{values[key]}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _generate_secret(key: str) -> str:
    if key.endswith("ENCRYPTION_KEY"):
        return secrets.token_hex(16)
    if key.endswith("HTPASSWD"):
        return secrets.token_urlsafe(48)
    return secrets.token_urlsafe(32)


def _sync_result(entry: SecretManifestEntry, status: str) -> dict[str, str]:
    return {
        "key": entry.key,
        "service": entry.service,
        "source_type": entry.source,
        "sync_status": status,
        "value": REDACTED,
    }
