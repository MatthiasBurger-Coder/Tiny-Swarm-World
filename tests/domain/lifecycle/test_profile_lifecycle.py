"""Strict scoped-profile intent and an explicitly unqualified product matrix."""
import json
import unittest

from tests.domain.lifecycle.test_models import manifest_fixture
from tiny_swarm_world.domain.lifecycle.models import InstallationProfileBinding, InstallationProfileIntent, ProxyRoute, installation_profile_name
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileCapabilityMatrix, ProfileLifecycleCheckpoint


def intent_fixture():
    manifest = manifest_fixture()
    binding = InstallationProfileBinding(profile_name=installation_profile_name(manifest.installation_id), routes=(
        ProxyRoute(device_name='tsw-proxy-10001', listen_address='127.0.0.1', listen_port=10001, connect_port=10001),))
    profile = InstallationProfileIntent(operation_id='a' * 32, operation_kind='setup', installation_id=manifest.installation_id,
        controller_revision='c' * 40, product_source_revision=manifest.product.revision, product_target_revision=None,
        incus_version='6.0.5', manifest_token=None, requested_services=manifest.requested_services,
        resolved_services=manifest.resolved_services, service_exposure={}, stack_ownership={}, profile=binding)
    return ManagerCreateIntent(profile=profile, endpoint_kind='incus_var_lib', image_fingerprint='e' * 64, base_profiles=('docker-swarm',),
        base_profiles_sha256='b' * 64, preservation_sha256='f' * 64, network='incusbr0', storage_pool='default',
        catalog_ports=(10001, 16080, 16081), cpu=2, memory='10GiB', disk='20GiB')


def admitted_fixture():
    return ProfileCapabilityMatrix.model_validate_json(json.dumps({'schema_version': 1,
        'capability': 'installation-scoped-incus-manager-profile', 'admitted_versions': [{
            'client_version': '6.0.5', 'server_version': '6.0.5', 'fixture_source_revision': 'c' * 40,
            'fixture_sha256': 'd' * 64}]}))


class ProfileIntentTests(unittest.TestCase):
    def test_complete_intent_and_checkpoint_roundtrip_do_not_assert_installation_completion(self):
        intent = intent_fixture()
        self.assertEqual(ManagerCreateIntent.model_validate_json(intent.model_dump_json()), intent)
        checkpoint = ProfileLifecycleCheckpoint(intent=intent, observation_sha256='1' * 64, stage='completed',
            previous_stage='completed', instance_uuid='11111111-1111-1111-1111-111111111111')
        self.assertFalse(checkpoint.settled)
        self.assertEqual(ProfileLifecycleCheckpoint.model_validate_json(checkpoint.model_dump_json()), checkpoint)
        self.assertTrue(checkpoint.model_copy(update={'installation_committed': True}).settled)
        self.assertEqual(intent.attachments(), ('docker-swarm', intent.profile.profile.profile_name))
        self.assertEqual(set(intent.devices()), {'tsw-proxy-10001'})

    def test_default_empty_capability_never_guesses_support(self):
        matrix = ProfileCapabilityMatrix(schema_version=1, admitted_versions=())
        for version in ('6.0.5', '6.0', '6.0.6', 'unknown'):
            self.assertFalse(matrix.admits(version, version))
        self.assertTrue(admitted_fixture().admits('6.0.5', '6.0.5'))
        self.assertFalse(admitted_fixture().admits('6.0.5', '6.0.6'))

    def test_shared_profile_unknown_fields_bad_routes_and_coerced_resources_refuse(self):
        original = intent_fixture().model_dump(mode='json')
        mutations: tuple[dict[str, object], ...] = (
            {'base_profiles': ['docker-swarm-manager']}, {'base_profiles': []},
            {'base_profiles': ['docker-swarm', 'docker-swarm']}, {'cpu': True}, {'cpu': '2'},
            {'catalog_ports': [10001, 10001]}, {'catalog_ports': [16080]},
            {'image_fingerprint': 'images:ubuntu/24.04'}, {'memory': 'auto'}, {'unexpected': True},
        )
        for changes in mutations:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ManagerCreateIntent.model_validate_json(json.dumps({**original, **changes}))
