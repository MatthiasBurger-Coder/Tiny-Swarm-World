import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.services.credential_resolution import CredentialResolutionService
from tiny_swarm_world.domain.configuration import default_configuration_contract
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.infrastructure.adapters.repositories.installer_configuration_repository import (
    InstallerConfigurationRepository,
)


def valid_environment():
    keys = tuple(item.key for item in default_configuration_contract().requirements if item.required)
    return CredentialResolutionService().resolve_bootstrap(keys).values


class TestInstallerConfigurationRepository(unittest.TestCase):
    def test_static_files_and_environment_are_validated_without_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(Path('infra/config'), root / 'config')
            env_file = root / 'operator.env'
            env_file.write_text('TSW_SETUP_MAX_CONCURRENCY=1\n', encoding='utf-8')
            environment = {'TSW_SETUP_MAX_CONCURRENCY': '3'}
            snapshot = InstallerConfigurationRepository(
                repository_root=Path.cwd(), infra_root=root,
                operator_env_file=env_file, environment=environment, service_profile='default',
            ).load()
            environment['TSW_SETUP_MAX_CONCURRENCY'] = '7'
            env_file.write_text('TSW_SETUP_MAX_CONCURRENCY=9\n', encoding='utf-8')
            self.assertEqual('3', snapshot.environment['TSW_SETUP_MAX_CONCURRENCY'])
            with self.assertRaises(TypeError):
                snapshot.environment['TSW_SETUP_MAX_CONCURRENCY'] = '5'
            self.assertNotIn('TSW_SETUP_MAX_CONCURRENCY', repr(snapshot))

    def test_malformed_selected_late_stack_and_provider_are_rejected(self):
        for filename in ('compose/swagger/docker-compose.yml', 'node-providers/provider_config.yaml',
                         'ports.yaml', 'secrets/infisical-secrets.yaml'):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(Path('infra/config'), root / 'config')
                (root / 'config' / filename).write_text('invalid: [private-marker', encoding='utf-8')
                with self.assertRaises(ValueError) as raised:
                    InstallerConfigurationRepository(
                        repository_root=Path.cwd(), infra_root=root, operator_env_file=None,
                        environment={}, service_profile='default',
                    ).load()
                self.assertNotIn('private-marker', str(raised.exception))

    def test_unselected_infisical_compose_does_not_block_default_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(Path('infra/config'), root / 'config')
            (root / 'config/compose/infisical/docker-compose.yml').write_text('invalid: [', encoding='utf-8')
            InstallerConfigurationRepository(
                repository_root=Path.cwd(), infra_root=root, operator_env_file=None,
                environment={}, service_profile='default',
            ).load()

    def test_invalid_platform_and_setup_inputs_fail_before_lifecycle(self):
        for key, value in (
            ('TSW_LXC_DOCKER_REGISTRY_MIRROR', 'http://localhost:5000'),
            ('TSW_SETUP_MAX_CONCURRENCY', '0'),
            ('TSW_SETUP_WORKFLOW_TIMEOUT_SECONDS', 'nan'),
            ('TSW_SETUP_HEARTBEAT_INTERVAL_SECONDS', 'inf'),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                InstallerConfigurationRepository.validate_environment(
                    {**valid_environment(), key: value}, stack_names=('portainer',), include_setup=True,
                )

    def test_bootstrap_values_required_and_only_explicit_consumer_key_deferred(self):
        environment = valid_environment()
        environment.pop('TSW_JENKINS_ADMIN_PASSWORD')
        InstallerConfigurationRepository.validate_environment(
            environment, stack_names=('jenkins', 'infisical'),
            deferred_keys=('TSW_JENKINS_ADMIN_PASSWORD',),
        )
        with self.assertRaises(ValueError):
            InstallerConfigurationRepository.validate_environment(environment, stack_names=('jenkins',))
        environment.pop('TSW_INFISICAL_ENCRYPTION_KEY')
        with self.assertRaises(ValueError):
            InstallerConfigurationRepository.validate_environment(
                environment, stack_names=('jenkins', 'infisical'),
                deferred_keys=('TSW_JENKINS_ADMIN_PASSWORD',),
            )

    def test_optional_absent_operator_file_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            InstallerConfigurationRepository.validate_operator_source(
                Path(directory) / 'absent.env', HostEnvironmentKind.NATIVE_LINUX,
            )

    def test_original_operator_permissions_are_not_bypassed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'operator.env'
            path.write_text('TSW_SETUP_MAX_CONCURRENCY=2\n', encoding='utf-8')
            path.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'storage is unsafe'):
                InstallerConfigurationRepository.validate_operator_source(path, HostEnvironmentKind.NATIVE_LINUX)
            path.chmod(0o600)
            InstallerConfigurationRepository.validate_operator_source(path, HostEnvironmentKind.NATIVE_LINUX)
            with patch('tiny_swarm_world.infrastructure.adapters.repositories.installer_configuration_repository.SecretStorageProbe.effective_identity', return_value=(os.geteuid() + 1, os.getegid())):
                with self.assertRaises(ValueError):
                    InstallerConfigurationRepository.validate_operator_source(path, HostEnvironmentKind.NATIVE_LINUX)
            link = Path(directory) / 'link.env'
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                InstallerConfigurationRepository.validate_operator_source(link, HostEnvironmentKind.NATIVE_LINUX)
