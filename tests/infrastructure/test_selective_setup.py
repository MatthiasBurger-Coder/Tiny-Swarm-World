"""Local composition regressions; all credentials below are synthetic fixtures."""

import os
import asyncio
import unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.lifecycle.selection import plan_selection
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.infrastructure import composition
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.application.services.deployment.workflows import DeploymentWorkflowStatus
from tiny_swarm_world.application.services.setup.workflow import SetupWorkflow, SetupWorkflowPhase, SetupWorkflowStatus


ROOT = Path(__file__).resolve().parents[2]


class SetupObservationCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def test_ineligible_state_builds_no_observer_runner_or_runtime_profile(self):
        state = Mock(observation_required=False)
        with patch.object(composition, "build_process_runner") as runner, \
             patch.object(composition._runtime, "resolve_runtime_profile") as resolve:
            await composition.complete_setup_selection_state(state, None)
        runner.assert_not_called()
        resolve.assert_not_called()

    async def test_facade_uses_resolved_backend_and_existing_process_runner(self):
        state = Mock(observation_required=True)
        request = Mock()
        backend = composition.ManagedLxcBackend.INCUS
        with patch.object(composition, "build_process_runner") as runner, \
             patch.object(composition._runtime, "resolve_runtime_profile", return_value=SimpleNamespace(backend=backend)) as resolve, \
             patch("tiny_swarm_world.infrastructure.composition_lifecycle.complete_setup_selection_state", new_callable=AsyncMock) as finish:
            await composition.complete_setup_selection_state(state, request)
        resolve.assert_called_once_with(state.plan.service_preset, request)
        finish.assert_awaited_once_with(state, backend, runner.return_value)

    async def test_runtime_observer_is_injected_without_import_time_or_constructor_commands(self):
        from tiny_swarm_world.infrastructure.composition_lifecycle import complete_setup_selection_state

        state = Mock(observation_required=True, observe_new_components=AsyncMock())
        runner = Mock()
        with patch("tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway.LxcManagerShellGateway") as gateway, \
             patch("tiny_swarm_world.infrastructure.adapters.update.lxc_runtime_observer.LxcUpdateRuntimeObserver") as observer:
            await complete_setup_selection_state(state, composition.ManagedLxcBackend.INCUS, runner)
        self.assertEqual(gateway.call_args.kwargs["timeout_seconds"], 10)
        self.assertIs(gateway.call_args.kwargs["process_runner"], runner)
        observer.assert_called_once_with(gateway.return_value)
        state.observe_new_components.assert_awaited_once_with(observer.return_value)
        runner.run_text.assert_not_called()


class MinimalApplyExecutionTests(unittest.IsolatedAsyncioTestCase):
    def build_minimal(self, events):
        with (patch.dict(os.environ, {'TSW_PORTAINER_ADMIN_PASSWORD': 'synthetic-portainer-value'}, clear=True),
              patch.object(composition, 'LxcSwarmRuntime') as swarm,
              patch.object(composition, 'LxcPortainerAdminClient') as admin,
              patch.object(composition, 'LxcPortainerHttpClient') as api,
              patch.object(composition, 'RoutingEvidenceLocalRepository'),
              patch('tiny_swarm_world.infrastructure.composition_deployment.HostEnvironmentDetector') as detector):
            detector.return_value.detect.return_value.environment = HostEnvironmentKind.WSL2
            services = composition.build_lxc_deployment_services(backend=composition.ManagedLxcBackend.INCUS,
                resolved_services=('incus', 'portainer'))
        admin.return_value.can_authenticate.side_effect = lambda *args: events.append('auth') or True
        api.return_value.get_endpoint_id_by_name.side_effect = lambda *args: events.append('endpoint') or 7
        for check in services.workflows.apply.empty_selection_checks:
            check.max_attempts, check.wait_seconds = 1, 0
        for check in services.workflows.verify.checks:
            check.max_attempts, check.wait_seconds = 1, 0
            check.session = Mock()
            check.session.get.side_effect = lambda *args, **kwargs: events.append('readiness') or Mock(status_code=200)
        return services, swarm.return_value, admin.return_value, api.return_value

    def test_minimal_apply_checks_follow_verification_identity_not_bootstrap_position(self):
        from tiny_swarm_world.infrastructure.composition_deployment_selection import minimal_apply_checks
        from tiny_swarm_world.domain.deployment.service_stack_contract import DEFAULT_SERVICE_STACK_CONTRACTS

        admin = SimpleNamespace(verification_target_id='deployment:portainer-admin-access')
        endpoint = SimpleNamespace(verification_target_id='deployment:portainer-local-endpoint')
        unrelated = SimpleNamespace(verification_target_id='deployment:portainer-stack')
        canonical = next(item for item in DEFAULT_SERVICE_STACK_CONTRACTS if item.stack_name == 'portainer')

        self.assertEqual((admin, endpoint), minimal_apply_checks(
            ('incus', 'portainer'), None, (canonical,), (), (unrelated, endpoint, admin)))

    def test_minimal_apply_checks_fail_closed_for_missing_or_duplicate_identities(self):
        from tiny_swarm_world.infrastructure.composition_deployment_selection import minimal_apply_checks
        from tiny_swarm_world.domain.deployment.service_stack_contract import DEFAULT_SERVICE_STACK_CONTRACTS

        admin = SimpleNamespace(verification_target_id='deployment:portainer-admin-access')
        endpoint = SimpleNamespace(verification_target_id='deployment:portainer-local-endpoint')
        canonical = next(item for item in DEFAULT_SERVICE_STACK_CONTRACTS if item.stack_name == 'portainer')

        self.assertEqual((), minimal_apply_checks(
            ('incus', 'portainer'), None, (canonical,), (), (admin,)))
        self.assertEqual((), minimal_apply_checks(
            ('incus', 'portainer'), None, (canonical,), (), (admin, endpoint, endpoint)))

    async def test_actual_composed_minimal_apply_verifies_fresh_access_without_stack_mutation(self):
        events = []
        services, swarm, admin, api = self.build_minimal(events)
        result = await services.workflows.apply.run()
        self.assertEqual(result.status, DeploymentWorkflowStatus.COMPLETED)
        self.assertFalse(result.executed)
        self.assertEqual(events, ['auth', 'endpoint'])
        swarm.deploy_stack.assert_not_called()
        swarm.prepare_stack_assets.assert_not_called()
        admin.initialize_admin_user.assert_not_called()
        api.ensure_local_endpoint.assert_not_called()
        self.assertEqual(result.operation_result.outcome.value, 'success')

    async def test_noncanonical_foundation_contract_cannot_authorize_empty_apply(self):
        from tiny_swarm_world.domain.deployment.service_stack_contract import service_stack_contracts_for_profile

        canonical = service_stack_contracts_for_profile(ServiceStackProfile.DEFAULT, ('incus', 'portainer'))[0]
        with patch.object(composition, 'service_stack_contracts_for_profile',
                          return_value=(replace(canonical, required_services=('portainer',)),)):
            services, swarm, admin, api = self.build_minimal([])
        result = await services.workflows.apply.run()
        self.assertEqual(result.status, DeploymentWorkflowStatus.BLOCKED)
        admin.can_authenticate.assert_not_called()
        api.get_endpoint_id_by_name.assert_not_called()
        swarm.deploy_stack.assert_not_called()

    async def exercise_cli_commit(self, failure=None):
        from tests.domain.lifecycle.test_models import manifest_fixture
        from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
        from tiny_swarm_world.infrastructure.adapters.cli.parser import parse_args
        from tiny_swarm_world.infrastructure.adapters.cli.selective_setup import run_selective_setup
        from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository

        events = []
        services, swarm, admin, api = self.build_minimal(events)
        if failure == 'auth':
            admin.can_authenticate.side_effect = lambda *args: events.append('auth') or False
        elif failure == 'endpoint':
            api.get_endpoint_id_by_name.side_effect = lambda *args: events.append('endpoint') or 0
        elif failure == 'cancel':
            api.get_endpoint_id_by_name.side_effect = asyncio.CancelledError()
        elif failure == 'readiness':
            services.workflows.verify.checks[0].session.get.return_value = Mock(status_code=503)
            services.workflows.verify.checks[0].session.get.side_effect = None
        runtime = SetupWorkflow((SetupWorkflowPhase('deployment apply', services.workflows.apply.run),
                                 SetupWorkflowPhase('deployment verify', services.workflows.verify.run)),
                                live_consent=LiveConsent(True, True))

        async def run_runtime(*args, **kwargs):
            return await runtime.run()

        with TemporaryDirectory() as directory:
            lifecycle = InstallationLifecycleService(JsonManifestRepository(Path(directory) / 'manifest.json'), NativeComponentCatalog(ROOT))
            components = tuple(component for service in lifecycle.catalog.load().services
                               if service.service_id in ('incus', 'portainer') for component in service.components)
            manifest = manifest_fixture().model_copy(update={'components': components})

            def commit():
                events.append('commit')
                lifecycle.manifests.save(manifest, expected_token=None)

            state = SimpleNamespace(commit=Mock(side_effect=commit))
            module = 'tiny_swarm_world.infrastructure.adapters.cli.selective_setup.composition.'
            with (patch(module + 'build_installation_lifecycle_service', return_value=lifecycle),
                  patch(module + 'prepare_setup_selection_state', AsyncMock(return_value=state)),
                  patch(module + 'complete_setup_selection_state', AsyncMock(side_effect=lambda *args: events.append('observe'))),
                  patch(module + 'run_setup_with_terminal_status', AsyncMock(side_effect=run_runtime))):
                args = parse_args(['setup', 'run', '--minimal', '--live', '--approve-live', '--json'])
                if failure == 'cancel':
                    with self.assertRaises(asyncio.CancelledError):
                        await run_selective_setup(args, LiveConsent(True, True))
                    result = None
                else:
                    result = await run_selective_setup(args, LiveConsent(True, True))
            if failure is None:
                self.assertEqual(result.status, SetupWorkflowStatus.COMPLETED)
                self.assertEqual(events, ['auth', 'endpoint', 'readiness', 'observe', 'commit'])
                state.commit.assert_called_once_with()
                self.assertEqual(lifecycle.manifests.load().manifest, manifest)
            else:
                state.commit.assert_not_called()
                self.assertIsNone(lifecycle.manifests.load().manifest)
                self.assertNotIn('observe', events)
                if result is not None:
                    self.assertNotEqual(result.status, SetupWorkflowStatus.COMPLETED)
        swarm.deploy_stack.assert_not_called()
        admin.initialize_admin_user.assert_not_called()
        api.ensure_local_endpoint.assert_not_called()

    async def test_minimal_cli_commits_once_only_after_apply_and_complete_final_verification(self):
        await self.exercise_cli_commit()

    async def test_minimal_cli_auth_endpoint_final_verification_and_cancellation_prevent_commit(self):
        for failure in ('auth', 'endpoint', 'readiness', 'cancel'):
            with self.subTest(failure=failure):
                await self.exercise_cli_commit(failure)


class SelectedImageExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_composed_bootstrap_and_swagger_forward_exact_pins_to_remote_compose(self):
        import shlex
        import subprocess
        from tiny_swarm_world.domain.lifecycle.portainer_upgrade import SOURCE_VERSION, images
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.swarm_stack_runtime import LxcSwarmStackRuntime
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT

        portainer = images(SOURCE_VERSION)
        swagger = next(service for service in NativeComponentCatalog(ROOT).load().services if service.service_id == 'swagger')
        pins = {'TSW_PORTAINER_IMAGE': portainer['portainer'], 'TSW_PORTAINER_AGENT_IMAGE': portainer['portainer-agent']}
        pins.update({IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT[name]: f'{identity.image_repository}@{identity.image_digest}'
                     for name, identity in swagger.update_transitions[0].source_versions.items()})
        for selected in (('incus', 'portainer'), ('incus', 'portainer', 'swagger')):
            with self.subTest(selected=selected):
                shell = Mock(return_value=subprocess.CompletedProcess([], 0, stdout='', stderr=''))
                runtime = LxcSwarmStackRuntime(remote_stack_root='/remote/stacks', service_list_timeout_seconds=30,
                    run_manager_shell=shell, run_node_shell=Mock(), prepare_stack_assets=Mock(), ensure_stack_prerequisites=Mock())
                environment = {**pins, 'TSW_PORTAINER_ADMIN_PASSWORD': 'synthetic-portainer-value',
                               'TSW_NEXUS_IMAGE': 'sonatype/nexus3:excluded-test-value'}
                with (patch.dict(os.environ, environment, clear=True),
                      patch.object(composition, 'LxcSwarmRuntime', return_value=runtime),
                      patch('tiny_swarm_world.infrastructure.composition_deployment.HostEnvironmentDetector') as detector):
                    detector.return_value.detect.return_value.environment = HostEnvironmentKind.WSL2
                    services = composition.build_lxc_deployment_services(backend=composition.ManagedLxcBackend.INCUS,
                        resolved_services=selected)
                await services.workflows.bootstrap.steps[0].run()
                if 'swagger' in selected:
                    swagger_step = next(step for step in services.workflows.apply.steps
                                        if getattr(step, 'verification_target_id', '') == 'deployment:swagger-stack')
                    await swagger_step.run()
                deployments = [call.args[0] for call in shell.call_args_list if 'docker stack deploy' in call.args[0]]
                self.assertEqual(len(deployments), 2 if 'swagger' in selected else 1)
                for script in deployments:
                    tokens = shlex.split(script)
                    actual = dict(token.split('=', 1) for token in tokens[:tokens.index('docker')])
                    stack = tokens[-1]
                    expected = {name: pin for name, pin in pins.items()
                                if name.startswith('TSW_PORTAINER_') == (stack == 'portainer')}
                    self.assertEqual(actual, {'TSW_REMOTE_STACK_ROOT': '/remote/stacks', **expected})
                    self.assertNotIn('TSW_NEXUS_IMAGE', actual)
                uploads = [call.kwargs['input_text'] for call in shell.call_args_list if 'input_text' in call.kwargs]
                self.assertTrue(any('${TSW_PORTAINER_IMAGE:-' in content and '${TSW_PORTAINER_AGENT_IMAGE:-' in content
                                    for content in uploads))


class SelectiveSetupCompositionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = NativeComponentCatalog(ROOT).load()
        self.environment = {
            "TSW_PORTAINER_ADMIN_PASSWORD": "synthetic-portainer-value",
        }

    def test_setup_forwards_resolved_selection_to_every_builder(self):
        plan = plan_selection(self.catalog, ("swagger", "sonarqube"))
        builders = (
            "_build_preflight_service_for_request",
            "_build_artifact_readiness_gate",
            "_build_platform_services_for_request",
            "build_artifact_services_for_provider",
            "_build_deployment_services_for_request",
            "ComposeFileRepositoryYaml",
        )
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, self.environment, clear=True))
            mocks = {
                name: stack.enter_context(patch.object(composition, name))
                for name in builders
            }
            stack.enter_context(patch.object(composition, "build_host_preparation_service"))
            services = composition.build_setup_services(
                LiveConsent(live_flag=False), selection_plan=plan,
            )

        self.assertTrue(services.workflows.run.phases)
        for name, builder in mocks.items():
            with self.subTest(builder=name):
                builder.assert_called_once()
                self.assertEqual(
                    plan.resolved_services,
                    builder.call_args.kwargs["resolved_services"],
                )
        mocks["ComposeFileRepositoryYaml"].return_value.validate_and_snapshot.assert_called_once_with(
            ("portainer", "sonarqube", "swagger"),
        )

    def test_selective_preflight_requires_only_selected_ports_and_secrets(self):
        plan = plan_selection(self.catalog, minimal=True)
        configuration = composition._preflight_configuration_for_provider(
            ServiceStackProfile.SERVICE_ACCESS, None,
            host_environment=HostEnvironmentKind.NATIVE_LINUX,
            resolved_services=plan.resolved_services,
        )

        self.assertEqual(("Portainer",), configuration.setup_manifest.service_names)
        self.assertEqual((10001,), tuple(item.port for item in configuration.required_ports))
        self.assertEqual(
            ("TSW_PORTAINER_ADMIN_PASSWORD",),
            tuple(item.name for item in configuration.required_secrets),
        )

    def _build_deployment(self, selected, extra_environment=None):
        environment = {**self.environment, **(extra_environment or {})}
        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(composition, "LxcSwarmRuntime") as runtime,
            patch.object(composition, "InfisicalCliClient") as infisical,
            patch.object(composition, "HostEnvironmentDetector") as detector,
        ):
            detector.return_value.detect.return_value.environment = HostEnvironmentKind.NATIVE_LINUX
            services = composition.build_lxc_deployment_services(
                backend=composition.ManagedLxcBackend.INCUS,
                service_profile=ServiceStackProfile.SERVICE_ACCESS,
                resolved_services=selected,
            )
            for workflow in (services.workflows.bootstrap, services.workflows.apply):
                workflow.configuration_preparation()
            runtime.return_value.prepare_stack_assets.assert_not_called()
            runtime.return_value.apply_stack.assert_not_called()
            infisical.assert_not_called()
        return services

    def test_minimal_deployment_needs_no_nexus_or_optional_credentials(self):
        plan = plan_selection(self.catalog, minimal=True)
        services = self._build_deployment(plan.resolved_services)

        self.assertEqual(
            ("deployment:portainer-stack", "deployment:portainer-admin-access",
             "deployment:portainer-local-endpoint"),
            tuple(step.verification_target_id for step in services.workflows.bootstrap.steps),
        )
        self.assertEqual((), services.workflows.apply.steps)
        self.assertEqual(
            ('deployment:portainer-admin-access', 'deployment:portainer-local-endpoint'),
            tuple(check.verification_target_id for check in services.workflows.apply.empty_selection_checks),
        )
        self.assertEqual((), services.workflows.apply.pre_apply_checks)
        self.assertEqual(
            (), tuple(step.stack_name for step in services.workflows.apply.pre_apply_steps
                      if hasattr(step, "stack_name")),
        )
        self.assertEqual(
            ("deployment:portainer-service-readiness",),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_minimal_artifacts_exclude_nexus_auth_and_unselected_images(self):
        plan = plan_selection(self.catalog, minimal=True)
        with (
            patch.dict(os.environ, self.environment, clear=True),
            patch.object(composition, "build_process_runner") as runner,
        ):
            services = composition.build_lxc_artifact_services(
                backend=composition.ManagedLxcBackend.INCUS,
                resolved_services=plan.resolved_services,
            )
            runner.return_value.run_text.assert_not_called()

        self.assertEqual((), services.workflows.prepare.bootstrap_steps)
        self.assertFalse(services.workflows.prepare.requires_bootstrap)
        expected = {"artifacts:portainer-image", "artifacts:portainer-agent-image"}
        self.assertEqual(
            expected,
            {step.verification_target_id for step in services.workflows.prepare.steps},
        )
        self.assertEqual(
            expected,
            {check.verification_target_id for check in services.workflows.verify.checks},
        )

    def test_swagger_sonarqube_prepare_and_verify_only_selected_stacks(self):
        plan = plan_selection(self.catalog, ("swagger", "sonarqube"))
        services = self._build_deployment(plan.resolved_services, {
            "TSW_SONARQUBE_ADMIN_PASSWORD": "synthetic-sonar-admin-value!",
            "TSW_POSTGRES_PASSWORD": "synthetic-sonar-postgres-value",
            "TSW_SONARQUBE_POSTGRES_PASSWORD": "synthetic-sonar-postgres-value",
        })

        self.assertEqual(
            ("deployment:sonarqube-stack", "deployment:sonarqube-admin-access",
             "deployment:swagger-stack"),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertEqual(
            ("swagger",),
            tuple(step.stack_name for step in services.workflows.apply.pre_apply_steps
                  if hasattr(step, "stack_name")),
        )
        self.assertEqual(
            ("deployment:portainer-service-readiness", "deployment:sonarqube-service-readiness",
             "deployment:swagger-service-readiness"),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )

    def test_jenkins_selection_keeps_transitive_nexus_bootstrap_and_readiness(self):
        plan = plan_selection(self.catalog, ("jenkins",))
        services = self._build_deployment(plan.resolved_services, {
            "TSW_NEXUS_ADMIN_PASSWORD": "synthetic-nexus-value",
            "TSW_JENKINS_ADMIN_PASSWORD": "synthetic-jenkins-value",
        })

        self.assertEqual(
            "deployment:nexus-stack",
            services.workflows.bootstrap.steps[-1].verification_target_id,
        )
        self.assertEqual(
            ("deployment:jenkins-stack",),
            tuple(step.verification_target_id for step in services.workflows.apply.steps),
        )
        self.assertEqual(
            ("deployment:portainer-service-readiness", "deployment:nexus-service-readiness",
             "deployment:jenkins-service-readiness"),
            tuple(check.verification_target_id for check in services.workflows.verify.checks),
        )
