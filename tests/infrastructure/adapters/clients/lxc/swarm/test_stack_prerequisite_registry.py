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
        run_manager_shell = Mock()
        registry = StackPrerequisiteRegistry()
        resolver = _FakeTlsResolver()
        self.addCleanup(resolver.close)
        resolver.resolve = Mock(wraps=resolver.resolve)

        registry.ensure_traefik_tls_secrets(
            "cert",
            "key",
            external_secret_exists=Mock(return_value=True),
            run_manager_shell=run_manager_shell,
            tls_contract_resolver=resolver,
        )

        run_manager_shell.assert_not_called()
        resolver.resolve.assert_not_called()


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
