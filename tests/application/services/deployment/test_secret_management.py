import json
import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.application.services.deployment.secret_management import (
    InfisicalSecretSyncStep,
    SecretConsumptionVerifier,
    SecretDiscoveryStep,
    SecretEvidenceWriter,
    SecretManagementBlocker,
    SecretManifestEntry,
    SecretManifestRenderer,
    SecretRedactor,
)


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

            entries = SecretManifestRenderer(manifest).run()

            self.assertEqual("TSW_POSTGRES_PASSWORD", entries[0].key)
            self.assertEqual("keep_existing", entries[0].policy)

    def test_committed_manifest_tracks_traefik_tls_secret_names_without_values(self):
        entries = SecretManifestRenderer(Path("config/secrets/infisical-secrets.yaml")).run()
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
        entries = SecretManifestRenderer(Path("config/secrets/infisical-secrets.yaml")).run()
        entries_by_key = {entry.key: entry for entry in entries}

        entry = entries_by_key["TSW_INFISICAL_BOOTSTRAP_TOKEN"]

        self.assertEqual("infisical_bootstrap_identity", entry.source)
        self.assertFalse(entry.required)

    def test_committed_manifest_tracks_required_infisical_login_identity(self):
        entries = SecretManifestRenderer(Path("config/secrets/infisical-secrets.yaml")).run()
        entries_by_key = {entry.key: entry for entry in entries}

        entry = entries_by_key["TSW_INFISICAL_LOGIN_EMAIL"]

        self.assertEqual("infisical", entry.service)
        self.assertEqual("placeholder_only", entry.type)
        self.assertEqual("placeholder_only", entry.source)
        self.assertTrue(entry.required)

    def test_secret_discovery_classifies_managed_placeholder_and_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docker-compose.yml").write_text(
                "POSTGRES_PASSWORD: ${TSW_POSTGRES_PASSWORD}\n"
                "password: " + "admin" + "Password123" + "\\n",
                encoding="utf-8",
            )
            discovery = SecretDiscoveryStep(
                repo_root=root,
                manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),),
            )

            with self.assertRaises(SecretManagementBlocker):
                discovery.run()

            classifications = {finding.classification for finding in discovery.findings}
            self.assertIn("generated_secret", classifications)
            self.assertIn("blocker", classifications)

    def test_redactor_redacts_values_and_assignments(self):
        redactor = SecretRedactor(("actual-secret",))

        redacted = redactor.redact({"line": "PASSWORD=actual-secret", "safe": "hello"})

        self.assertEqual("PASSWORD=<redacted>", redacted["line"])
        self.assertEqual("hello", redacted["safe"])

    def test_infisical_sync_creates_missing_and_keeps_existing(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / "generated.local.env"
            cli = _FakeInfisicalCli(existing={"TSW_EXISTING_PASSWORD"})
            sync = InfisicalSecretSyncStep(
                cli=cli,
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
                manifest_entries=(_entry("TSW_API_SYNC_PASSWORD"),),
                generated_local_env=env_file,
            )

            sync.run()

            self.assertEqual([("tiny-swarm-world", "local")], cli.ensured)
            self.assertIn("TSW_API_SYNC_PASSWORD", cli.values)

    def test_missing_required_external_secret_blocks(self):
        sync = InfisicalSecretSyncStep(
            cli=_FakeInfisicalCli(),
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
            sync = InfisicalSecretSyncStep(cli=cli, manifest_entries=(_entry("TSW_STABLE_PASSWORD"),), generated_local_env=env_file)
            sync.run()
            first = env_file.read_text(encoding="utf-8")
            sync_again = InfisicalSecretSyncStep(cli=_FakeInfisicalCli(), manifest_entries=(_entry("TSW_STABLE_PASSWORD"),), generated_local_env=env_file)
            sync_again.run()

            self.assertEqual(first, env_file.read_text(encoding="utf-8"))

    def test_rendered_env_files_are_gitignored(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8")

        self.assertIn("/.tiny-swarm/", gitignore)
        self.assertIn("*.local.env", gitignore)

    def test_evidence_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            discovery = SecretDiscoveryStep(repo_root=root, manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),))
            discovery.run()
            sync = InfisicalSecretSyncStep(cli=_FakeInfisicalCli(), manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),), generated_local_env=root / "generated.local.env")
            sync.run()
            consumption = SecretConsumptionVerifier(manifest_entries=(_entry("TSW_POSTGRES_PASSWORD"),), stack_environment={"postgres": {"TSW_POSTGRES_PASSWORD": "secret-value"}})
            consumption.run()
            writer = SecretEvidenceWriter(evidence_dir=root / "evidence", discovery=discovery, sync=sync, consumption=consumption)

            writer.run()

            evidence = json.loads((root / "evidence" / "infisical-sync-result.json").read_text(encoding="utf-8"))
            self.assertEqual("<redacted>", evidence["results"][0]["value"])
            self.assertNotIn("secret-value", (root / "evidence" / "secret-consumption-report.md").read_text(encoding="utf-8"))


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


if __name__ == "__main__":
    unittest.main()
