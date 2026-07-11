import json
import tempfile
import unittest
from pathlib import Path

from tests.support.sonar_safe_literals import operator_credential, sample_text

from tiny_swarm_world.application.services.deployment.secret_management import (
    FixedEnvSecretSource,
    InfisicalSecretSyncStep,
    InfisicalSecretStore,
    SecretConsumptionVerifier,
    SecretDiscoveryStep,
    SecretEvidenceWriter,
    SecretManagementBlocker,
    SecretManifestEntry,
    SecretManifestRenderer,
    SecretRedactor,
    SecretSyncUseCase,
)
from tiny_swarm_world.infrastructure.adapters.file_management.local_file_storage import (
    LocalFileStorage,
)

_PULSAR_COMPOSE_FIXTURE = Path("infra/config/compose/pulsar/docker-compose.yml")
_STORAGE = LocalFileStorage()


class TestSecretManagement(unittest.TestCase):
    def test_manifest_schema_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "infisical-secrets.yaml"
            manifest.write_text(
                "secrets:\n"
                "  - key: TSW_POSTGRES_PASSWORD\n"
                "    service: postgres\n"
                "    type: generated_secret\n"
                "    environment: local\n"
                "    description: PostgreSQL password\n"
                "    source: generated_local_secret\n"
                "    required: true\n",
                encoding="utf-8",
            )

            entries = SecretManifestRenderer(_STORAGE, manifest).run()

            self.assertEqual("TSW_POSTGRES_PASSWORD", entries[0].key)
            self.assertEqual("keep_existing", entries[0].policy)

    def test_committed_manifest_tracks_traefik_tls_secret_names_without_values(self):
        entries = SecretManifestRenderer(
            _STORAGE,
            Path("infra/config/secrets/infisical-secrets.yaml"),
        ).run()
        entries_by_key = {entry.key: entry for entry in entries}

        for key in (
            "TSW_TRAEFIK_TLS_CERT_SECRET_NAME",
            "TSW_TRAEFIK_TLS_KEY_SECRET_NAME",
        ):
            with self.subTest(key=key):
                entry = entries_by_key[key]
                self.assertEqual("traefik", entry.service)
                self.assertEqual("external_user_secret", entry.type)
                self.assertEqual("external_user_secret", entry.source)
                self.assertTrue(entry.required)
                self.assertNotIn("BEGIN", entry.description)
                self.assertNotIn("REDACTED", entry.description)

    def test_committed_manifest_keeps_infisical_bootstrap_token_optional(self):
        entries = SecretManifestRenderer(
            _STORAGE,
            Path("infra/config/secrets/infisical-secrets.yaml"),
        ).run()
        entries_by_key = {entry.key: entry for entry in entries}

        entry = entries_by_key["TSW_INFISICAL_BOOTSTRAP_TOKEN"]

        self.assertEqual("infisical_bootstrap_identity", entry.source)
        self.assertFalse(entry.required)

    def test_committed_manifest_marks_infisical_redis_password_required(self):
        entries = SecretManifestRenderer(
            _STORAGE,
            Path("infra/config/secrets/infisical-secrets.yaml"),
        ).run()
        entries_by_key = {entry.key: entry for entry in entries}

        entry = entries_by_key["TSW_INFISICAL_REDIS_PASSWORD"]

        self.assertEqual("infisical", entry.service)
        self.assertEqual("generated_secret", entry.type)
        self.assertEqual("generated_local_secret", entry.source)
        self.assertTrue(entry.required)

    def test_manifest_entries_expose_ownership_storage_and_lifecycle(self):
        entries = SecretManifestRenderer(
            _STORAGE,
            Path("infra/config/secrets/infisical-secrets.yaml"),
        ).run()
        entries_by_key = {entry.key: entry for entry in entries}

        generated = entries_by_key["TSW_NEXUS_ADMIN_PASSWORD"]
        external = entries_by_key["TSW_TRAEFIK_TLS_CERT_SECRET_NAME"]
        bootstrap = entries_by_key["TSW_INFISICAL_BOOTSTRAP_TOKEN"]

        self.assertEqual("python_installer", generated.owner)
        self.assertEqual(".tiny-swarm-world/local/live-installation.env", generated.storage)
        self.assertEqual("generated_when_missing_and_kept_existing", generated.lifecycle)
        self.assertEqual("operator", external.owner)
        self.assertEqual("external_docker_secret_or_operator_env", external.storage)
        self.assertEqual("operator_created_and_rotated", external.lifecycle)
        self.assertEqual("infisical_sync", bootstrap.owner)
        self.assertEqual(".tiny-swarm/secrets/generated.local.env", bootstrap.storage)
        self.assertEqual("created_during_infisical_sync_and_reused", bootstrap.lifecycle)

    def test_committed_manifest_tracks_required_infisical_login_identity(self):
        entries = SecretManifestRenderer(
            _STORAGE,
            Path("infra/config/secrets/infisical-secrets.yaml"),
        ).run()
        entries_by_key = {entry.key: entry for entry in entries}

        entry = entries_by_key["TSW_INFISICAL_LOGIN_EMAIL"]

        self.assertEqual("infisical", entry.service)
        self.assertEqual("placeholder_only", entry.type)
        self.assertEqual("placeholder_only", entry.source)
        self.assertTrue(entry.required)

    def test_pulsar_compose_bootstrap_does_not_create_secret_inventory_blocker(self):
        entries = SecretManifestRenderer(
            _STORAGE,
            Path("infra/config/secrets/infisical-secrets.yaml"),
        ).run()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_repo_fixture(root, "docker-compose.yml", _PULSAR_COMPOSE_FIXTURE.read_text(encoding="utf-8"))
            discovery = SecretDiscoveryStep(
                storage=_STORAGE,
                repo_root=root,
                manifest_entries=entries,
            )

            findings = discovery.run()

        self.assertFalse([finding for finding in findings if finding.classification == "blocker"])

    def test_secret_discovery_classifies_managed_placeholder_and_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docker-compose.yml").write_text(
                "POSTGRES_PASSWORD: ${TSW_POSTGRES_PASSWORD}\n"
                "password: " + "admin" + "Password123" + "\\n",
                encoding="utf-8",
            )
            discovery = SecretDiscoveryStep(
                storage=_STORAGE,
                repo_root=root,
                manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),),
            )

            with self.assertRaises(SecretManagementBlocker):
                discovery.run()

            classifications = {finding.classification for finding in discovery.findings}
            self.assertIn("generated_secret", classifications)
            self.assertIn("blocker", classifications)

    def test_secret_discovery_treats_credential_item_refs_as_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_repo_fixture(
                root,
                "ports.yaml",
                "credential_item_ref: platform/portainer\n"
                'credential_note: "Open Infisical item"\n',
            )
            discovery = SecretDiscoveryStep(storage=_STORAGE, repo_root=root)

            findings = discovery.run()

        classifications = {finding.key: finding.classification for finding in findings}
        self.assertEqual("placeholder_only", classifications["credential_item_ref"])
        self.assertEqual("false_positive", classifications["credential_note"])
        self.assertNotIn("blocker", set(classifications.values()))

    def test_redactor_redacts_values_and_assignments(self):
        redactor = SecretRedactor((operator_credential(),))
        key = sample_text("PASS", "WORD")

        redacted = redactor.redact({"line": f"{key}={operator_credential()}", "safe": "hello"})

        self.assertEqual(f"{key}=<redacted>", redacted["line"])
        self.assertEqual("hello", redacted["safe"])

    def test_infisical_sync_creates_missing_and_keeps_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "generated.local.env"
            cli = _FakeInfisicalCli(existing={"TSW_EXISTING_PASSWORD"})
            sync = InfisicalSecretSyncStep(
                cli=cli,
                storage=_STORAGE,
                manifest_entries=(
                    _entry("TSW_NEW_PASSWORD"),
                    _entry("TSW_EXISTING_PASSWORD"),
                ),
                generated_local_env=env_file,
            )

            sync.run()

            statuses = {item["key"]: item["sync_status"] for item in sync.results}
            self.assertEqual("created", statuses["TSW_NEW_PASSWORD"])
            self.assertEqual("kept_existing", statuses["TSW_EXISTING_PASSWORD"])
            self.assertIn("TSW_NEW_PASSWORD", cli.values)

    def test_infisical_sync_uses_api_client_even_when_local_cli_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "generated.local.env"
            cli = _FakeInfisicalCli(available=False)
            sync = InfisicalSecretSyncStep(
                cli=cli,
                storage=_STORAGE,
                manifest_entries=(_entry("TSW_API_SYNC_PASSWORD"),),
                generated_local_env=env_file,
            )

            sync.run()

            self.assertEqual([("tiny-swarm-world", "local")], cli.ensured)
            self.assertIn("TSW_API_SYNC_PASSWORD", cli.values)

    def test_fixed_mode_syncs_complete_file(self):
        with tempfile.TemporaryDirectory() as directory:
            fixed_file = Path(directory) / "fixed.env"
            fixed_file.write_text(
                "export TSW_FIXED_ONE_PASSWORD='fixed-one'\n"
                "export TSW_FIXED_TWO_PASSWORD='fixed-two'\n",
                encoding="utf-8",
            )
            cli = _FakeInfisicalCli()
            sync = InfisicalSecretSyncStep(
                cli=cli,
                storage=_STORAGE,
                manifest_entries=(
                    _entry("TSW_FIXED_ONE_PASSWORD"),
                    _entry("TSW_FIXED_TWO_PASSWORD"),
                ),
                fixed_env_file=fixed_file,
                mode="fixed",
            )

            sync.run()
            result = sync.verify()

        self.assertEqual("fixed-one", cli.values["TSW_FIXED_ONE_PASSWORD"])
        self.assertEqual("fixed-two", cli.values["TSW_FIXED_TWO_PASSWORD"])
        self.assertEqual(
            ("TSW_FIXED_ONE_PASSWORD", "TSW_FIXED_TWO_PASSWORD"),
            sync.checked_secret_keys,
        )
        self.assertEqual("fixed", result.evidence["selected_mode"])
        self.assertEqual("2", result.evidence["synchronized_entry_count"])
        self.assertNotIn("fixed-one", str(result.evidence))

    def test_fixed_mode_blocks_missing_key(self):
        with tempfile.TemporaryDirectory() as directory:
            fixed_file = Path(directory) / "fixed.env"
            fixed_file.write_text(
                "export TSW_PRESENT_PASSWORD='fixed-one'\n",
                encoding="utf-8",
            )
            sync = InfisicalSecretSyncStep(
                cli=_FakeInfisicalCli(),
                storage=_STORAGE,
                manifest_entries=(
                    _entry("TSW_PRESENT_PASSWORD"),
                    _entry("TSW_MISSING_PASSWORD"),
                ),
                fixed_env_file=fixed_file,
                mode="fixed",
            )

            with self.assertRaisesRegex(SecretManagementBlocker, "TSW_MISSING_PASSWORD"):
                sync.run()

    def test_fixed_mode_blocks_empty_value(self):
        with tempfile.TemporaryDirectory() as directory:
            fixed_file = Path(directory) / "fixed.env"
            fixed_file.write_text(
                "export TSW_EMPTY_PASSWORD=''\n",
                encoding="utf-8",
            )
            sync = InfisicalSecretSyncStep(
                cli=_FakeInfisicalCli(),
                storage=_STORAGE,
                manifest_entries=(_entry("TSW_EMPTY_PASSWORD"),),
                fixed_env_file=fixed_file,
                mode="fixed",
            )

            with self.assertRaisesRegex(SecretManagementBlocker, "TSW_EMPTY_PASSWORD"):
                sync.run()

    def test_infisical_sync_failure_blocks_without_secret_value(self):
        fixed_value = operator_credential()
        with tempfile.TemporaryDirectory() as directory:
            fixed_file = Path(directory) / "fixed.env"
            fixed_file.write_text(
                f"export TSW_FAILING_PASSWORD='{fixed_value}'\n",
                encoding="utf-8",
            )
            sync = SecretSyncUseCase(
                store=InfisicalSecretStore(_FailingInfisicalCli()),
                storage=_STORAGE,
                manifest_entries=(_entry("TSW_FAILING_PASSWORD"),),
                fixed_source=FixedEnvSecretSource(_STORAGE, fixed_file),
                mode="fixed",
            )

            with self.assertRaises(SecretManagementBlocker) as raised:
                sync.run()

        self.assertIn("TSW_FAILING_PASSWORD", str(raised.exception))
        self.assertNotIn(fixed_value, str(raised.exception))

    def test_missing_required_external_secret_blocks(self):
        sync = InfisicalSecretSyncStep(
            cli=_FakeInfisicalCli(),
            storage=_STORAGE,
            manifest_entries=(
                SecretManifestEntry(
                    key="TSW_EXTERNAL_API_KEY",
                    service="external",
                    type="external_user_secret",
                    environment="local",
                    description="External API key",
                    source="external_user_secret",
                    required=True,
                ),
            ),
        )

        with self.assertRaises(SecretManagementBlocker):
            sync.run()

    def test_generated_secret_stable_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "generated.local.env"
            cli = _FakeInfisicalCli()
            sync = InfisicalSecretSyncStep(
                cli=cli,
                storage=_STORAGE,
                manifest_entries=(_entry("TSW_STABLE_PASSWORD"),),
                generated_local_env=env_file,
            )
            sync.run()
            first = env_file.read_text(encoding="utf-8")
            sync_again = InfisicalSecretSyncStep(
                cli=_FakeInfisicalCli(),
                storage=_STORAGE,
                manifest_entries=(_entry("TSW_STABLE_PASSWORD"),),
                generated_local_env=env_file,
            )
            sync_again.run()

            self.assertEqual(first, env_file.read_text(encoding="utf-8"))

    def test_rendered_env_files_are_gitignored(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8")

        self.assertIn("/.tiny-swarm/", gitignore)
        self.assertIn("*.local.env", gitignore)

    def test_secret_consumption_blocks_when_required_reference_is_missing(self):
        consumption = SecretConsumptionVerifier(
            manifest_entries=(_entry("TSW_REQUIRED_PASSWORD"),),
            stack_environment={},
        )

        consumption.run()
        result = consumption.verify()

        self.assertEqual("blocked", result.status.value)
        self.assertEqual("1", result.evidence["missing_required_count"])
        self.assertEqual("required_consumer_missing", result.evidence["reason"])

    def test_evidence_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            discovery = SecretDiscoveryStep(
                storage=_STORAGE,
                repo_root=root,
                manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),),
            )
            discovery.run()
            sync = InfisicalSecretSyncStep(
                cli=_FakeInfisicalCli(),
                storage=_STORAGE,
                manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),),
                generated_local_env=root / "generated.local.env",
            )
            sync.run()
            consumption = SecretConsumptionVerifier(manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),), stack_environment={"postgres": {"TSW_POSTGRES_PASSWORD": operator_credential()}})
            consumption.run()
            writer = SecretEvidenceWriter(
                storage=_STORAGE,
                evidence_dir=root / "evidence",
                discovery=discovery,
                sync=sync,
                consumption=consumption,
            )

            writer.run()

            evidence = json.loads((root / "evidence" / "infisical-sync-result.json").read_text(encoding="utf-8"))
            self.assertEqual("generated", evidence["mode"])
            self.assertIn("TSW_POSTGRES_PASSWORD", evidence["checked_secret_keys"])
            self.assertIn("TSW_POSTGRES_PASSWORD", evidence["synchronized_secret_keys"])
            self.assertNotIn("value", evidence["results"][0])
            self.assertNotIn(operator_credential(), (root / "evidence" / "secret-consumption-report.md").read_text(encoding="utf-8"))


def _entry(key: str) -> SecretManifestEntry:
    return SecretManifestEntry(
        key=key,
        service="service",
        type="generated_secret",
        environment="local",
        description="Generated secret",
        source="generated_local_secret",
        required=True,
    )


def _write_repo_fixture(root: Path, file_name: str, content: str) -> Path:
    resolved_root = root.resolve(strict=True)
    destination = (resolved_root / file_name).resolve()
    if destination.parent != resolved_root or destination.name != file_name:
        raise ValueError("fixture destination must stay inside the temporary root")
    destination.write_text(content, encoding="utf-8")
    return destination


class _FakeInfisicalCli:
    def __init__(self, existing: set[str] | None = None, available: bool = True):
        self.existing = existing or set()
        self.available = available
        self.values: dict[str, str] = {}
        self.ensured: list[tuple[str, str]] = []

    def is_available(self) -> bool:
        return self.available

    def run_bootstrap(self, args: tuple[str, ...]):
        raise AssertionError("not used")

    def ensure_project_environment(self, project: str, environment: str) -> None:
        self.ensured.append((project, environment))

    def secret_exists(self, key: str, *, project: str, environment: str) -> bool:
        return key in self.existing

    def set_secret(self, key: str, value: str, *, project: str, environment: str) -> None:
        self.values[key] = value
        self.existing.add(key)


class _FailingInfisicalCli(_FakeInfisicalCli):
    def set_secret(self, key: str, value: str, *, project: str, environment: str) -> None:
        raise RuntimeError(f"sync failed for {key}")


if __name__ == "__main__":
    unittest.main()
