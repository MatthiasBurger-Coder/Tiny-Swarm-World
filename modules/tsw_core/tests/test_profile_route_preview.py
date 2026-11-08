"""Actual read-only CLI desired-route projection; requires canonical S06 exposure."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tiny_swarm_world.__main__ import main
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest, InstallationProfileBinding, SwarmOwnership, installation_profile_name, migrate_manifest_v1
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
from tiny_swarm_world.application.services.profile_setup import proxy_routes_from_setup_manifest
from tiny_swarm_world.infrastructure.composition import build_installation_lifecycle_service
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from modules.tsw_core.tests.application.services.test_lifecycle import adoption_fixture

_ROOT = Path(__file__).resolve().parents[3]


class ProfileRoutePreviewTests(unittest.IsolatedAsyncioTestCase):
    async def preview(self, lifecycle, mode):
        with patch('tiny_swarm_world.infrastructure.adapters.cli.selection.build_installation_lifecycle_service', return_value=lifecycle), \
                patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.ensure_common_executable_paths') as paths, \
                patch('tiny_swarm_world.infrastructure.adapters.cli.dispatcher.build_application_logger') as logger, \
                patch('tiny_swarm_world.infrastructure.composition.build_setup_services') as setup, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            await main(['setup', 'run', '--services', 'swagger', '--swagger-exposure', mode, '--preview', '--json'])
        paths.assert_not_called()
        logger.assert_not_called()
        setup.assert_not_called()
        return json.loads(output.getvalue())['routes']

    async def test_fresh_internal_and_published_preview_is_pure_and_uses_same_source_listen_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lifecycle = build_installation_lifecycle_service(_ROOT)
            lifecycle.manifests = JsonManifestRepository(root / 'state/manifest.json')
            with patch.dict(os.environ, {'TSW_LXC_PROXY_LISTEN_ADDRESS': '127.0.0.1'}):
                internal = await self.preview(lifecycle, 'internal')
                published = await self.preview(lifecycle, 'published')
            self.assertEqual({route['listen_port'] for route in internal['after']}, {10001})
            self.assertEqual({route['listen_port'] for route in published['after']}, {10001, 16080, 16081})
            self.assertEqual(internal['before'], [])
            self.assertFalse(internal['baseline_bound'])
            self.assertFalse(internal['runtime_observed'])
            self.assertEqual(internal['listen_address'], '127.0.0.1')
            self.assertEqual(internal['additions'], internal['after'])
            self.assertEqual(list(root.iterdir()), [])

    async def test_existing_bound_before_after_additions_and_removals_are_exact_and_preserve_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lifecycle = build_installation_lifecycle_service(_ROOT)
            lifecycle.manifests = JsonManifestRepository(root / 'state/manifest.json')
            catalog = lifecycle.catalog.load()
            baseline = migrate_manifest_v1(adoption_fixture(catalog))
            plan = ServiceSelectionService(lifecycle.manifests, lifecycle.catalog).preview(requested=('swagger',))
            canonical = default_setup_manifest(service_profile=plan.service_preset, resolved_services=plan.resolved_services,
                                               service_exposure={'swagger': 'published'})
            routes = proxy_routes_from_setup_manifest(canonical, '127.0.0.1')
            components = tuple(component for service in catalog.services if service.service_id in plan.resolved_services
                               for component in service.components)
            before = InstallationManifest.model_validate_json(baseline.model_copy(update={
                'requested_services': plan.requested_services, 'resolved_services': plan.resolved_services,
                'selection_reasons': plan.selection_reasons, 'components': components,
                'service_exposure': {'swagger': 'published'}, 'stack_ownership': {'swagger': SwarmOwnership()},
                'installation_profile': InstallationProfileBinding(profile_name=installation_profile_name(baseline.installation_id), routes=routes),
            }).model_dump_json())
            lifecycle.manifests.save(before, expected_token=None)
            original = lifecycle.manifests.path.read_bytes()
            with patch.dict(os.environ, {'TSW_LXC_PROXY_LISTEN_ADDRESS': '0.0.0.0'}):
                internal = await self.preview(lifecycle, 'internal')
            self.assertEqual(internal['listen_address'], '127.0.0.1')
            self.assertEqual({route['listen_port'] for route in internal['before']}, {10001, 16080, 16081})
            self.assertEqual({route['listen_port'] for route in internal['after']}, {10001})
            self.assertEqual({route['listen_port'] for route in internal['removals']}, {16080, 16081})
            self.assertEqual(internal['additions'], [])
            payload = before.model_dump()
            binding = before.installation_profile
            assert binding is not None
            payload.update(service_exposure={'swagger': 'internal'}, installation_profile=binding.model_copy(
                update={'routes': tuple(route for route in routes if route.listen_port == 10001)}))
            snapshot = lifecycle.manifests.load()
            lifecycle.manifests.save(InstallationManifest.model_validate(payload), expected_token=snapshot.token)
            internal_bytes = lifecycle.manifests.path.read_bytes()
            published = await self.preview(lifecycle, 'published')
            self.assertEqual({route['listen_port'] for route in published['additions']}, {16080, 16081})
            self.assertEqual(published['removals'], [])
            self.assertEqual(lifecycle.manifests.path.read_bytes(), internal_bytes)
            self.assertNotEqual(original, internal_bytes)
