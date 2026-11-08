"""Public composition compatibility: omit absent options, retain private identity."""
from itertools import product
from typing import Any
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure import composition_runtime as runtime


class CompositionRequestOptionsTests(unittest.TestCase):
    def test_platform_optional_arguments_preserve_legacy_none_omission_and_context_identity(self):
        marker: Any = object()
        selection = ('incus', 'portainer', 'swagger')
        exposure = {'swagger': 'internal'}
        for provider, ui, trace, operation in product((None, marker), repeat=4):
            with self.subTest(provider=provider, ui=ui, trace=trace, operation=operation), \
                    patch.object(runtime, 'build_platform_services', return_value=marker) as build:
                actual = runtime._build_platform_services_for_request(
                    'service-access', None, provider, ui=ui, trace_correlation_id=trace,
                    resolved_services=selection, service_exposure=exposure, profile_operation=operation)
            self.assertIs(actual, marker)
            expected: dict[str, Any] = {'service_profile': 'service-access', 'live_consent': None,
                        'allow_wsl_windows_filesystem': False,
                        'resolved_services': selection, 'service_exposure': exposure}
            if provider is not None:
                expected['node_provider_request'] = provider
            if ui is not None or trace is not None:
                expected.update(ui=ui, trace_correlation_id=trace)
            if operation is not None:
                expected['profile_operation'] = operation
            self.assertEqual(build.call_args.kwargs, expected)
            if operation is not None:
                self.assertIs(build.call_args.kwargs['profile_operation'], operation)

    def test_deployment_context_and_selection_are_forwarded_together_without_none_keywords(self):
        marker: Any = object()
        selection = ('incus', 'portainer', 'swagger')
        exposure = {'swagger': 'internal'}
        for provider, ui, progress, operation in product((None, marker), repeat=4):
            with self.subTest(provider=provider, ui=ui, progress=progress, operation=operation), \
                    patch.object(runtime, 'build_deployment_services_for_provider', return_value=marker) as build:
                actual = runtime._build_deployment_services_for_request(
                    'service-access', provider, ui=ui, progress=progress, resolved_services=selection,
                    service_exposure=exposure, profile_operation=operation)
            self.assertIs(actual, marker)
            expected: dict[str, Any] = {'service_profile': 'service-access', 'node_provider_request': provider,
                        'resolved_services': selection, 'service_exposure': exposure}
            if ui is not None:
                expected['ui'] = ui
            if progress is not None:
                expected['progress'] = progress
            if operation is not None:
                expected['profile_operation'] = operation
            self.assertEqual(build.call_args.kwargs, expected)
            if operation is not None:
                self.assertIs(build.call_args.kwargs['profile_operation'], operation)
