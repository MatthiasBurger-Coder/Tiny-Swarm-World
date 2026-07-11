from __future__ import annotations

import json
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Mapping

from tiny_swarm_world.application.ports.clients.port_infisical_cli import PortInfisicalCli
from tiny_swarm_world.application.ports.file_management.port_local_file_storage import (
    PortLocalFileStorage,
)
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
SecretMode = Literal["generated", "fixed", "infisical"]

REDACTED = "<redacted>"
DEFAULT_MANIFEST_PATH = Path("infra/config/secrets/infisical-secrets.yaml")
DEFAULT_FIXED_LOCAL_ENV = Path(".tiny-swarm-world/local/fixed-secrets.env")
DEFAULT_BOOTSTRAP_LOCAL_ENV = Path(".tiny-swarm/secrets/bootstrap.local.env")
DEFAULT_GENERATED_LOCAL_ENV = Path(".tiny-swarm/secrets/generated.local.env")
DEFAULT_EVIDENCE_DIR = Path(".tiny-swarm/evidence/secrets")
SECRET_MODES: tuple[SecretMode, ...] = ("generated", "fixed", "infisical")
SECRET_KEY_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]*(?:PASSWORD|TOKEN|SECRET|API_KEY|CREDENTIAL|HTPASSWD|KEY)[A-Z0-9_]*\b")
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?P<key>[a-z_][a-z0-9_-]*)\s*[:=]\s*(?P<value>[^\n#]+)",
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
    "CREDENTIAL_NOTE",
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
    owner: str = ""
    storage: str = ""
    lifecycle: str = ""


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


class FixedEnvSecretSource:
    def __init__(self, storage: PortLocalFileStorage, env_file: Path = DEFAULT_FIXED_LOCAL_ENV) -> None:
        self.storage = storage
        self.env_file = env_file

    def values_for(self, manifest_entries: tuple[SecretManifestEntry, ...]) -> dict[str, str]:
        if not self.storage.exists(self.env_file):
            raise SecretManagementBlocker(
                "fixed_secret_file_missing",
                f"Fixed secret file is missing: {self.env_file.as_posix()}",
            )
        values = _read_env_file(self.storage, self.env_file)
        entries_by_key = {entry.key: entry for entry in manifest_entries}
        required_keys = tuple(entry.key for entry in manifest_entries if entry.required)
        missing = [key for key in required_keys if key not in values]
        if missing:
            raise SecretManagementBlocker("fixed_secret_key_missing", f"Fixed secret key is missing: {missing[0]}")
        empty = [key for key, value in values.items() if key in entries_by_key and not value.strip()]
        if empty:
            raise SecretManagementBlocker("fixed_secret_value_empty", f"Fixed secret value is empty: {empty[0]}")
        return {key: value for key, value in values.items() if key in entries_by_key}


class InfisicalSecretStore:
    def __init__(self, cli: PortInfisicalCli) -> None:
        self.cli = cli

    def ensure_scope(self, project: str, environment: str) -> None:
        self.cli.ensure_project_environment(project, environment)

    def secret_exists(self, key: str, *, project: str, environment: str) -> bool:
        return self.cli.secret_exists(key, project=project, environment=environment)

    def set_secret(self, key: str, value: str, *, project: str, environment: str) -> None:
        self.cli.set_secret(key, value, project=project, environment=environment)


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
    def __init__(self, storage: PortLocalFileStorage, manifest_path: Path = DEFAULT_MANIFEST_PATH) -> None:
        self.storage = storage
        self.manifest_path = manifest_path

    def run(self) -> tuple[SecretManifestEntry, ...]:
        payload = self.storage.load_yaml(self.manifest_path)
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

    def __init__(
        self,
        *,
        storage: PortLocalFileStorage,
        repo_root: Path = Path("."),
        manifest_entries: tuple[SecretManifestEntry, ...] = (),
    ) -> None:
        self.storage = storage
        self.repo_root = repo_root
        self.manifest_entries = manifest_entries
        self._findings: tuple[SecretFinding, ...] = ()

    @property
    def findings(self) -> tuple[SecretFinding, ...]:
        return self._findings

    def run(self) -> tuple[SecretFinding, ...]:
        managed_keys = {entry.key: entry for entry in self.manifest_entries}
        findings: list[SecretFinding] = []
        snapshots = self.storage.scan_text_files(
            self.repo_root,
            suffixes=frozenset(SCAN_SUFFIXES),
            skip_parts=frozenset(SKIP_PARTS),
        )
        for snapshot in snapshots:
            for line_number, line in enumerate(snapshot.text.splitlines(), start=1):
                findings.extend(
                    _classify_line(snapshot.path, self.repo_root, line_number, line, managed_keys)
                )
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
        storage: PortLocalFileStorage,
        manifest_entries: tuple[SecretManifestEntry, ...],
        generated_local_env: Path = DEFAULT_GENERATED_LOCAL_ENV,
        fixed_env_file: Path = DEFAULT_FIXED_LOCAL_ENV,
        mode: SecretMode = "generated",
        project: str = "tiny-swarm-world",
        environment: str = "local",
        process_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.use_case = SecretSyncUseCase(
            store=InfisicalSecretStore(cli),
            storage=storage,
            manifest_entries=manifest_entries,
            generated_local_env=generated_local_env,
            fixed_source=FixedEnvSecretSource(storage, fixed_env_file),
            mode=mode,
            project=project,
            environment=environment,
            process_environment=process_environment,
        )
        self.results: list[dict[str, str]] = []
        self.mode = mode
        self.checked_secret_keys: tuple[str, ...] = ()
        self.synchronized_secret_keys: tuple[str, ...] = ()

    def run(self) -> None:
        self.use_case.run()
        self.results = self.use_case.results
        self.checked_secret_keys = self.use_case.checked_secret_keys
        self.synchronized_secret_keys = self.use_case.synchronized_secret_keys

    def verify(self) -> VerificationResult:
        return self.use_case.verify()


class SecretSyncUseCase:
    def __init__(
        self,
        *,
        store: InfisicalSecretStore,
        storage: PortLocalFileStorage,
        manifest_entries: tuple[SecretManifestEntry, ...],
        generated_local_env: Path = DEFAULT_GENERATED_LOCAL_ENV,
        fixed_source: FixedEnvSecretSource | None = None,
        mode: SecretMode = "generated",
        project: str = "tiny-swarm-world",
        environment: str = "local",
        process_environment: Mapping[str, str] | None = None,
    ) -> None:
        if mode not in SECRET_MODES:
            raise ValueError(f"Unsupported secret mode: {mode}")
        self.store = store
        self.storage = storage
        self.manifest_entries = manifest_entries
        self.generated_local_env = generated_local_env
        self.fixed_source = fixed_source or FixedEnvSecretSource(storage)
        self.mode = mode
        self.project = project
        self.environment = environment
        self.process_environment = process_environment or {}
        self.results: list[dict[str, str]] = []
        self.checked_secret_keys: tuple[str, ...] = ()
        self.synchronized_secret_keys: tuple[str, ...] = ()

    def run(self) -> None:
        try:
            self.store.ensure_scope(self.project, self.environment)
        except Exception as exc:
            raise SecretManagementBlocker(
                "infisical_sync_failed",
                "Infisical secret sync failed while preparing scope.",
            ) from exc
        if self.mode == "fixed":
            self._run_fixed()
        elif self.mode == "infisical":
            self._run_infisical_only()
        else:
            self._run_generated()

    def _entry_value(self, entry: SecretManifestEntry, generated_values: dict[str, str]) -> str:
        value = self.process_environment.get(entry.key) or generated_values.get(entry.key, "")
        if not value and entry.source == "generated_local_secret":
            value = _generate_secret(entry.key)
            generated_values[entry.key] = value
        if value and entry.source in {"generated_local_secret", "infisical_bootstrap_identity"}:
            generated_values.setdefault(entry.key, value)
        return value

    def _run_generated(self) -> None:
        generated_values = _read_env_file(self.storage, self.generated_local_env)
        self.checked_secret_keys = tuple(entry.key for entry in self.manifest_entries if entry.required)
        for entry in self.manifest_entries:
            value = self._entry_value(entry, generated_values)
            if entry.required and not value:
                raise SecretManagementBlocker("blocker", f"Required secret value is missing: {entry.key}")
            self._sync_entry(entry, value, generated_values)
        _write_env_file(self.storage, self.generated_local_env, generated_values)
        self.synchronized_secret_keys = tuple(
            result["key"]
            for result in self.results
            if result["sync_status"] in {"created", "updated", "kept_existing"}
        )

    def _run_fixed(self) -> None:
        fixed_values = self.fixed_source.values_for(self.manifest_entries)
        self.checked_secret_keys = tuple(entry.key for entry in self.manifest_entries if entry.required)
        for entry in self.manifest_entries:
            value = fixed_values.get(entry.key, "")
            if not value:
                self.results.append(_sync_result(entry, "skipped_missing_optional"))
                continue
            self._set_entry(entry, value, status_if_existing="updated")
        self.synchronized_secret_keys = tuple(
            result["key"]
            for result in self.results
            if result["sync_status"] in {"created", "updated"}
        )

    def _run_infisical_only(self) -> None:
        checked: list[str] = []
        for entry in self.manifest_entries:
            if not entry.required:
                continue
            checked.append(entry.key)
            if not self._secret_exists(entry):
                raise SecretManagementBlocker(
                    "infisical_secret_missing",
                    f"Required Infisical secret is missing: {entry.key}",
                )
            self.results.append(_sync_result(entry, "verified_existing"))
        self.checked_secret_keys = tuple(checked)
        self.synchronized_secret_keys = ()

    def _sync_entry(
        self,
        entry: SecretManifestEntry,
        value: str,
        generated_values: dict[str, str],
    ) -> None:
        if not value:
            self.results.append(_sync_result(entry, "skipped_missing_optional"))
            return
        exists = self._secret_exists(entry)
        if exists and entry.policy == "keep_existing":
            self.results.append(_sync_result(entry, "kept_existing"))
            return
        if exists and entry.policy == "rotate":
            value = _generate_secret(entry.key)
            generated_values[entry.key] = value
        self._set_entry(entry, value, status_if_existing="updated" if exists else "created")

    def _secret_exists(self, entry: SecretManifestEntry) -> bool:
        try:
            return self.store.secret_exists(entry.key, project=self.project, environment=self.environment)
        except Exception as exc:
            raise SecretManagementBlocker(
                "infisical_sync_failed",
                f"Infisical secret sync failed while checking key: {entry.key}",
            ) from exc

    def _set_entry(self, entry: SecretManifestEntry, value: str, *, status_if_existing: str) -> None:
        try:
            exists = self.store.secret_exists(entry.key, project=self.project, environment=self.environment)
            self.store.set_secret(entry.key, value, project=self.project, environment=self.environment)
        except Exception as exc:
            raise SecretManagementBlocker(
                "infisical_sync_failed",
                f"Infisical secret sync failed while writing key: {entry.key}",
            ) from exc
        self.results.append(_sync_result(entry, status_if_existing if exists else "created"))

    def verify(self) -> VerificationResult:
        synced = [
            result
            for result in self.results
            if result["sync_status"] in {"created", "updated", "kept_existing", "verified_existing"}
        ]
        missing = [result for result in self.results if result["sync_status"] == "skipped_missing_optional"]
        return VerificationResult(
            target_id=InfisicalSecretSyncStep.verification_target_id,
            status=VerificationStatus.VERIFIED,
            message="Infisical managed entries were synchronized idempotently.",
            evidence={
                "phase": "verify",
                "selected_mode": self.mode,
                "checked_entry_count": str(len(self.checked_secret_keys)),
                "synchronized_entry_count": str(len(self.synchronized_secret_keys)),
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
        status = VerificationStatus.BLOCKED if missing else VerificationStatus.VERIFIED
        message = (
            "Required managed config consumption references are missing."
            if missing
            else "Managed config consumption references were verified without exposing values."
        )
        evidence = {
            "phase": "verify",
            "configured_ref_count": str(len(self.report)),
            "missing_required_count": str(len(missing)),
        }
        if missing:
            evidence["reason"] = "required_consumer_missing"
        return VerificationResult(
            target_id=self.verification_target_id,
            status=status,
            message=message,
            evidence=evidence,
        )


class SecretEvidenceWriter:
    verification_target_id = "deployment:managed-config-evidence"
    deployment_target_id = verification_target_id

    def __init__(
        self,
        *,
        storage: PortLocalFileStorage,
        evidence_dir: Path = DEFAULT_EVIDENCE_DIR,
        discovery: SecretDiscoveryStep,
        sync: InfisicalSecretSyncStep,
        consumption: SecretConsumptionVerifier,
    ) -> None:
        self.storage = storage
        self.evidence_dir = evidence_dir
        self.discovery = discovery
        self.sync = sync
        self.consumption = consumption

    def run(self) -> None:
        now = datetime.now(UTC).isoformat()
        inventory = {
            "generated_at": now,
            "findings": [finding.__dict__ for finding in self.discovery.findings],
        }
        sync_result = {
            "checked_secret_keys": list(self.sync.checked_secret_keys),
            "generated_at": now,
            "mode": self.sync.mode,
            "results": self.sync.results,
            "synchronized_secret_keys": list(self.sync.synchronized_secret_keys),
        }
        consumption_lines = ["# Secret Consumption Report", ""]
        for item in self.consumption.report:
            consumption_lines.append(f"- {item['key']} ({item['service']}): {item['consumer_status']}")
        self.storage.write_text(
            self.evidence_dir / "secret-inventory.json",
            json.dumps(inventory, indent=2, sort_keys=True),
            private=True,
        )
        self.storage.write_text(
            self.evidence_dir / "infisical-sync-result.json",
            json.dumps(sync_result, indent=2, sort_keys=True),
            private=True,
        )
        self.storage.write_text(
            self.evidence_dir / "secret-consumption-report.md",
            "\n".join(consumption_lines) + "\n",
            private=True,
        )

    def verify(self) -> VerificationResult:
        paths = ("secret-inventory.json", "infisical-sync-result.json", "secret-consumption-report.md")
        existing = [name for name in paths if self.storage.exists(self.evidence_dir / name)]
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
    source = str(item.get("source", ""))
    return SecretManifestEntry(
        key=key,
        service=str(item.get("service", "")),
        type=entry_type,  # type: ignore[arg-type]
        environment=str(item.get("environment", "local")),
        description=str(item.get("description", "")),
        source=source,
        required=bool(item.get("required", False)),
        policy=policy,  # type: ignore[arg-type]
        owner=str(item.get("owner", _manifest_owner(source))),
        storage=str(item.get("storage", _manifest_storage(source))),
        lifecycle=str(item.get("lifecycle", _manifest_lifecycle(source))),
    )


def _manifest_owner(source: str) -> str:
    if source == "external_user_secret":
        return "operator"
    if source == "infisical_bootstrap_identity":
        return "infisical_sync"
    if source in {"generated_local_secret", "placeholder_only"}:
        return "python_installer"
    return "unknown"


def _manifest_storage(source: str) -> str:
    if source == "external_user_secret":
        return "external_docker_secret_or_operator_env"
    if source == "infisical_bootstrap_identity":
        return ".tiny-swarm/secrets/generated.local.env"
    if source in {"generated_local_secret", "placeholder_only"}:
        return ".tiny-swarm-world/local/live-installation.env"
    return "unknown"


def _manifest_lifecycle(source: str) -> str:
    if source == "external_user_secret":
        return "operator_created_and_rotated"
    if source == "infisical_bootstrap_identity":
        return "created_during_infisical_sync_and_reused"
    if source == "generated_local_secret":
        return "generated_when_missing_and_kept_existing"
    if source == "placeholder_only":
        return "operator_supplied_and_kept_existing"
    return "unknown"


def _classify_line(path: Path, repo_root: Path, line_number: int, line: str, managed_keys: dict[str, SecretManifestEntry]) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    relative = path.relative_to(repo_root).as_posix()
    for key in SECRET_KEY_PATTERN.findall(line):
        finding = _classify_secret_key(key, relative, line_number, managed_keys)
        if finding is not None:
            findings.append(finding)
    assignment = SECRET_ASSIGNMENT_PATTERN.search(line)
    if assignment:
        key = assignment.group("key")
        if not _is_secretish_name(key):
            return findings
        value = assignment.group("value").strip().strip('"\'')
        classification = _classify_secret_assignment(path, relative, line, key, value, managed_keys)
        findings.append(SecretFinding(key, classification, relative, line_number, redacted_value=REDACTED))
    return findings


def _classify_secret_key(
    key: str,
    relative: str,
    line_number: int,
    managed_keys: dict[str, SecretManifestEntry],
) -> SecretFinding | None:
    if any(false_key in key for false_key in FALSE_POSITIVE_KEYS):
        return SecretFinding(key, "false_positive", relative, line_number, reason="safe_symbol_name")
    if key in managed_keys:
        return SecretFinding(key, managed_keys[key].type, relative, line_number, service=managed_keys[key].service)
    if key.startswith("TSW_"):
        return SecretFinding(key, "external_user_secret", relative, line_number, reason="unmanaged_tsw_secret_reference")
    return None


def _classify_secret_assignment(
    path: Path,
    relative: str,
    line: str,
    key: str,
    value: str,
    managed_keys: dict[str, SecretManifestEntry],
) -> SecretClassification:
    if key in managed_keys or value in managed_keys or "_operator_secret_value" in value:
        return "managed_secret"
    if value.startswith("${") or "System.getenv" in value:
        return "placeholder_only"
    if key.upper() in FALSE_POSITIVE_ASSIGNMENTS:
        return "false_positive"
    if _is_secret_reference_assignment_key(key):
        return "placeholder_only"
    if any(marker in value.lower() for marker in SOURCE_MARKERS + PLACEHOLDER_MARKERS):
        return "placeholder_only"
    if relative.startswith("tests/") and ("assert" in line or "operator_credential" in line):
        return "placeholder_only"
    if path.suffix == ".py" and not value.startswith(("\"", "'")):
        return "false_positive"
    if value.startswith("/"):
        return "false_positive"
    if value and len(value) >= 6:
        return "blocker"
    return "false_positive"


def _is_secretish_name(key: str) -> bool:
    normalized = key.upper().replace("-", "_")
    if any(part in normalized for part in ("PASSWORD", "TOKEN", "SECRET", "API_KEY", "CREDENTIAL", "HTPASSWD")):
        return True
    return normalized.endswith("_KEY") and not normalized.endswith(("BY_KEY", "_KEYS"))


def _is_secret_reference_assignment_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized.endswith("_item_ref")


def _is_sensitive_key_or_assignment(value: str) -> bool:
    return bool(SECRET_ASSIGNMENT_PATTERN.search(value) or SECRET_KEY_PATTERN.search(value))


def _redact_assignment(value: str) -> str:
    return SECRET_ASSIGNMENT_PATTERN.sub(lambda match: f"{match.group('key')}={REDACTED}", value)


def _read_env_file(storage: PortLocalFileStorage, path: Path) -> dict[str, str]:
    text = storage.read_text(path)
    if text is None:
        return {}
    values: dict[str, str] = {}
    for line in text.splitlines():
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


def _write_env_file(storage: PortLocalFileStorage, path: Path, values: dict[str, str]) -> None:
    lines = ["# Generated by Tiny Swarm World. Do not commit."]
    for key in sorted(values):
        lines.append(f"export {key}='{values[key]}'")
    storage.write_text(path, "\n".join(lines) + "\n", private=True)


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
    }
