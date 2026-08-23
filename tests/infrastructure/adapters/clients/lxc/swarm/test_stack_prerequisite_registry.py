import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from tiny_swarm_world.domain.deployment import StackDefinition
from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.stack_prerequisite_registry import (
    StackPrerequisiteRegistry,
)
from tiny_swarm_world.domain.ingress import ResolvedTlsContract, TlsAuthorityMode


class TestStackPrerequisiteRegistry(unittest.TestCase):
    def test_registry_applies_network_and_sonarqube_strategies_in_order(self):
        run_manager_shell = Mock(
            side_effect=[
                subprocess.CompletedProcess([], 1),
                subprocess.CompletedProcess([], 0),
                subprocess.CompletedProcess([], 0),
            ]
        )
        ensure_network = Mock()
        ensure_tls = Mock()
        registry = StackPrerequisiteRegistry()
        definition = StackDefinition(
            name="sonarqube",
            compose_content=(
                "networks:\n"
                "  shared:\n"
                "    name: shared_overlay\n"
                "    external: true\n"
            ),
        )

        registry.ensure(
            "sonarqube",
            definition,
            ensure_external_overlay_network=ensure_network,
            ensure_traefik_tls_secrets=ensure_tls,
            run_manager_shell=run_manager_shell,
        )

        ensure_network.assert_called_once_with("shared_overlay")
        ensure_tls.assert_not_called()
        run_manager_shell.assert_called_once_with(
            "sysctl -w vm.max_map_count=524288 fs.file-max=131072 >/dev/null"
        )

    def test_traefik_tls_strategy_is_idempotent_when_secrets_exist(self):
        model = _SecretCommandModel({"cert", "key"})
        registry = StackPrerequisiteRegistry()
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)
        resolver.resolve = Mock(wraps=resolver.resolve)

        registry.ensure_traefik_tls_secrets(
            "cert",
            "key",
            external_secret_exists=Mock(return_value=True),
            run_manager_shell=model,
            tls_contract_resolver=resolver,
        )

        self.assertEqual(len(model.reconciliation_scripts), 0)
        resolver.resolve.assert_called_once_with()

    def test_traefik_tls_reconciliation_recovers_each_partial_pair_state(self):
        for initial_state, orphan_name in (({"cert"}, "cert"), ({"key"}, "key")):
            with self.subTest(initial_state=initial_state):
                state = set(initial_state)
                resolver = _FakeTlsResolver()
                self.addCleanup(resolver.close)

                model = _SecretCommandModel(state)

                StackPrerequisiteRegistry().ensure_traefik_tls_secrets(
                    "cert",
                    "key",
                    external_secret_exists=lambda name: name in state,
                    run_manager_shell=model,
                    tls_contract_resolver=resolver,
                )

                self.assertEqual(state, {"cert", "key"})
                self.assertIn(
                    f"docker secret rm -- {orphan_name}",
                    model.reconciliation_scripts[0],
                )

    def test_traefik_tls_second_create_failure_rolls_back_and_retry_converges(self):
        state: set[str] = set()
        model = _SecretCommandModel(state, fail_second_create_once=True)
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)

        registry = StackPrerequisiteRegistry()
        with self.assertRaises(subprocess.CalledProcessError):
            registry.ensure_traefik_tls_secrets(
                "cert",
                "key",
                external_secret_exists=lambda name: name in state,
                run_manager_shell=model,
                tls_contract_resolver=resolver,
            )
        self.assertEqual(state, set())

        registry.ensure_traefik_tls_secrets(
            "cert",
            "key",
            external_secret_exists=lambda name: name in state,
            run_manager_shell=model,
            tls_contract_resolver=resolver,
        )

        self.assertEqual(state, {"cert", "key"})
        self.assertIn("if ! key_id=$(docker secret create --label", model.reconciliation_scripts[0])
        self.assertIn('docker secret rm -- "$cert_id"', model.reconciliation_scripts[0])
        self.assertNotIn("certificate", model.reconciliation_scripts[0])
        self.assertNotIn("private-key", model.reconciliation_scripts[0])

    def test_traefik_tls_reconciliation_fails_closed_when_pair_cannot_be_verified(self):
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)

        with self.assertRaisesRegex(RuntimeError, "could not be verified"):
            StackPrerequisiteRegistry().ensure_traefik_tls_secrets(
                "cert",
                "key",
                external_secret_exists=lambda _name: False,
                run_manager_shell=Mock(return_value=subprocess.CompletedProcess([], 0)),
                tls_contract_resolver=resolver,
            )

    def test_rejects_unowned_existing_pair_and_duplicate_names(self):
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)
        with self.assertRaisesRegex(RuntimeError, "not a verified owned pair"):
            StackPrerequisiteRegistry().ensure_traefik_tls_secrets(
                "cert", "key",
                external_secret_exists=lambda _name: True,
                run_manager_shell=_SecretCommandModel({"cert", "key"}, owned=False),
                tls_contract_resolver=resolver,
            )

    def test_post_create_existence_failure_rolls_back_and_retry_converges(self):
        state: set[str] = set()
        model = _SecretCommandModel(state, hide_post_create_once=True)
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)
        registry = StackPrerequisiteRegistry()

        with self.assertRaisesRegex(RuntimeError, "could not be verified"):
            registry.ensure_traefik_tls_secrets(
                "cert", "key", external_secret_exists=model.exists,
                run_manager_shell=model, tls_contract_resolver=resolver,
            )
        self.assertEqual(state, set())

        registry.ensure_traefik_tls_secrets(
            "cert", "key", external_secret_exists=model.exists,
            run_manager_shell=model, tls_contract_resolver=resolver,
        )
        self.assertEqual(state, {"cert", "key"})

    def test_post_create_label_mismatch_rolls_back_and_retry_converges(self):
        state: set[str] = set()
        model = _SecretCommandModel(state, mismatch_post_create_once=True)
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)
        registry = StackPrerequisiteRegistry()

        with self.assertRaisesRegex(RuntimeError, "ownership could not be verified"):
            registry.ensure_traefik_tls_secrets(
                "cert", "key", external_secret_exists=model.exists,
                run_manager_shell=model, tls_contract_resolver=resolver,
            )
        self.assertEqual(state, set())

        registry.ensure_traefik_tls_secrets(
            "cert", "key", external_secret_exists=model.exists,
            run_manager_shell=model, tls_contract_resolver=resolver,
        )
        self.assertEqual(state, {"cert", "key"})
        with self.assertRaisesRegex(ValueError, "distinct"):
            StackPrerequisiteRegistry().ensure_traefik_tls_secrets(
                "same", "same", external_secret_exists=lambda _name: False,
                run_manager_shell=Mock(), tls_contract_resolver=resolver,
            )


class _FakeTlsResolver:
    def __init__(self):
        self._temporary = tempfile.TemporaryDirectory()
        root = Path(self._temporary.name)
        self.certificate = root / "tls.crt"
        self.key = root / "tls.key"
        self.ca = root / "ca.crt"
        self.certificate.write_bytes(b"certificate")
        self.key.write_bytes(b"private-key")
        self.ca.write_bytes(b"ca")

    def resolve(self):
        return ResolvedTlsContract(
            mode=TlsAuthorityMode.EXTERNAL,
            ca_certificate=self.ca,
            leaf_certificate=self.certificate,
            leaf_private_key=self.key,
            trust_bundle=self.ca,
            certificate_secret_name="cert",
            private_key_secret_name="key",
            lifecycle_fingerprint="0" * 64,
            certificate_bytes=b"certificate",
            private_key_bytes=b"private-key",
        )

    def close(self):
        self._temporary.cleanup()


class _SecretCommandModel:
    def __init__(
        self, state: set[str], *, owned: bool = True,
        fail_second_create_once: bool = False,
        hide_post_create_once: bool = False,
        mismatch_post_create_once: bool = False,
    ):
        self.state = state
        self.owned = owned
        self.fail_second_create_once = fail_second_create_once
        self.hide_post_create_once = hide_post_create_once
        self.mismatch_post_create_once = mismatch_post_create_once
        self.reconciliation_scripts: list[str] = []

    def exists(self, name: str) -> bool:
        if self.hide_post_create_once and self.state:
            self.hide_post_create_once = False
            return False
        return name in self.state

    def __call__(self, script: str, **kwargs):
        if "docker secret inspect --format" in script:
            name = script.rsplit("-- ", 1)[1]
            if self.mismatch_post_create_once and name in self.state:
                self.mismatch_post_create_once = False
                return subprocess.CompletedProcess([], 0, stdout="tiny-swarm-world|mismatch\n")
            labels = "tiny-swarm-world|" + "0" * 64 if self.owned and name in self.state else "|"
            return subprocess.CompletedProcess([], 0, stdout=labels + "\n")
        if script.startswith("docker secret rm -- idcert idkey"):
            self.state.clear()
            return subprocess.CompletedProcess([], 0)
        self.reconciliation_scripts.append(script)
        if self.fail_second_create_once:
            self.fail_second_create_once = False
            self.state.clear()
            raise subprocess.CalledProcessError(1, "manager-shell")
        self.state.clear()
        self.state.update(("cert", "key"))
        return subprocess.CompletedProcess([], 0, stdout="idcert|idkey\n")
