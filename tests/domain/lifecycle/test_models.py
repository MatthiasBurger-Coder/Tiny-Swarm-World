import json
import unittest
from uuid import uuid4

from pydantic import ValidationError

from tiny_swarm_world.domain.lifecycle.models import (
    ComponentState, CredentialReference, InstallationManifest, ProductIdentity, VersionIdentity,
)
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import decode_manifest
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


def manifest_fixture() -> InstallationManifest:
    return InstallationManifest(
        installation_id=str(uuid4()), host="native-linux", service_preset="default",
        product=ProductIdentity(release="0.2.0", revision="a" * 40, dependency_lock="sha256:" + "b" * 64),
        requested_services=("incus", "portainer"), resolved_services=("incus", "portainer"),
        components=(ComponentState(component_id="incus", service_id="incus", desired=VersionIdentity()),),
        credential_references=(CredentialReference(key="TSW_PORTAINER_ADMIN_PASSWORD", source="external_user_secret"),),
    )


class ManifestContractTests(unittest.TestCase):
    def test_current_schema_identity_migration_is_lossless(self):
        manifest = manifest_fixture()
        self.assertEqual(decode_manifest(manifest.model_dump_json().encode()), manifest)

    def test_unknown_legacy_future_and_corrupt_state_rejected_safely(self):
        for content in (b'{"schema_version":0}', b'{"schema_version":2}', b'{"schema_version":true}',
                        b'{}', b'[]', b'{', b'\xff', b'{"schema_version":1,"schema_version":1}'):
            with self.subTest(content=content), self.assertRaises(LifecycleStateError):
                decode_manifest(content)

    def test_catalog_version_types_are_not_coerced(self):
        original = manifest_fixture().model_dump(mode="json")
        for version in (True, 1.0, "1", 2):
            with self.subTest(version=version), self.assertRaises(LifecycleStateError):
                decode_manifest(json.dumps(dict(original, catalog_version=version)).encode())

    def test_invalid_and_secret_fields_never_echo_input(self):
        payload = manifest_fixture().model_dump(mode="json")
        for key, value in (("password", "SECRET_SENTINEL"), ("host", "kubernetes"), ("installation_id", "invalid")):
            invalid = dict(payload, **{key: value})
            with self.subTest(key=key), self.assertRaises(LifecycleStateError) as caught:
                decode_manifest(json.dumps(invalid).encode())
            self.assertNotIn("SECRET_SENTINEL", str(caught.exception))
        with self.assertRaises(ValidationError):
            CredentialReference.model_validate({"key": "TSW_PORTAINER_ADMIN_PASSWORD", "source": "external_user_secret", "value": "SECRET_SENTINEL"})

    def test_selection_foundations_duplicates_and_provenance(self):
        original = manifest_fixture().model_dump(mode="json")
        for change in (
            {"resolved_services": ["incus"]},
            {"requested_services": ["incus", "incus"]},
            {"requested_services": ["incus"]},
            {"selection_reasons": {"portainer": ["unknown"]}},
        ):
            with self.subTest(change=change), self.assertRaises(LifecycleStateError):
                decode_manifest(json.dumps(dict(original, **change)).encode())

    def test_versions_and_resolved_digest_drift_are_separate(self):
        desired = VersionIdentity(upstream_version="2.568.3", image_repository="registry/jenkins",
                                  image_tag="0.2.0", build_identity="0.2.0", image_digest="sha256:" + "a" * 64)
        component = ComponentState(component_id="jenkins", service_id="jenkins", desired=desired)
        self.assertEqual(component.drift(), ("observation_missing",))
        observed = desired.model_copy(update={"image_digest": "sha256:" + "b" * 64})
        self.assertEqual(component.model_copy(update={"observed": observed}).drift(), ("image_digest_mismatch",))
        self.assertEqual(component.model_copy(update={"observed": desired}).drift(), ())
        missing = desired.model_copy(update={"image_digest": None, "upstream_version": None})
        self.assertIn("upstream_version_unknown", component.model_copy(update={"observed": missing}).drift())
        self.assertIn("resolved_image_unknown", component.model_copy(update={"observed": missing}).drift())

    def test_image_identity_rejects_credentials_and_invalid_digest(self):
        for change in ({"image_repository": "user:SECRET@registry/image"}, {"image_digest": "sha256:short"}, {"image_tag": "tag"}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                VersionIdentity(**change)

class ManifestV2ContractTests(unittest.TestCase):
    def test_legacy_read_projection_and_explicit_migration_are_lossless(self):
        from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1

        original = manifest_fixture()
        raw = original.model_dump_json().encode()
        observed = decode_manifest(raw)
        self.assertEqual(observed.schema_version, 1)
        self.assertNotIn('service_exposure', json.loads(raw))
        self.assertEqual(observed.effective_exposure(), {})
        self.assertEqual(observed.model_dump_json().encode(), raw)
        upgraded = migrate_manifest_v1(observed)
        self.assertEqual(upgraded.schema_version, 2)
        self.assertIsNone(upgraded.installation_profile)
        self.assertEqual(upgraded.service_exposure, {})
        self.assertEqual(upgraded.stack_ownership, {})
        self.assertEqual(decode_manifest(upgraded.model_dump_json().encode()), upgraded)
        policy = {'schema_version', 'service_exposure', 'stack_ownership', 'installation_profile'}
        self.assertEqual({key: value for key, value in upgraded.model_dump().items() if key not in policy},
                         {key: value for key, value in original.model_dump().items() if key not in policy})
        self.assertEqual(migrate_manifest_v1(upgraded), upgraded)

    def test_schema_fields_presence_exact_types_and_unknown_ownership_are_refused(self):
        from tiny_swarm_world.domain.lifecycle.models import migrate_manifest_v1

        original = manifest_fixture().model_dump(mode='json')
        for field in ('service_exposure', 'stack_ownership', 'installation_profile'):
            with self.subTest(v1_field=field), self.assertRaises(LifecycleStateError):
                decode_manifest(json.dumps({**original, field: None}).encode())
        upgraded = migrate_manifest_v1(manifest_fixture()).model_dump(mode='json')
        for field in ('service_exposure', 'stack_ownership', 'installation_profile'):
            missing = dict(upgraded)
            missing.pop(field)
            with self.subTest(v2_missing=field), self.assertRaises(LifecycleStateError):
                decode_manifest(json.dumps(missing).encode())
        malformed: tuple[dict[str, object], ...] = (
            {'schema_version': True}, {'schema_version': 2.0}, {'service_exposure': None},
            {'stack_ownership': None}, {'service_exposure': {'swagger': 'internal'}},
            {'stack_ownership': {'portainer': {'owner': 'swarm'}}},
            {'installation_profile': {'project': 'foreign', 'profile_name': 'same-name', 'routes': []}},
            {'unrecognized': 'private-canary'})
        for changes in malformed:
            with self.subTest(changes=changes), self.assertRaises(LifecycleStateError) as error:
                decode_manifest(json.dumps({**upgraded, **changes}).encode())
            self.assertNotIn('private-canary', str(error.exception))

    def test_selected_swagger_and_authenticated_portainer_evidence_are_strict_values(self):
        from tests.application.services.test_lifecycle import adoption_fixture
        from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
        from tiny_swarm_world.infrastructure.project_paths import default_project_paths
        from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership, migrate_manifest_v1
        from tiny_swarm_world.domain.lifecycle.selection import plan_selection

        catalog = NativeComponentCatalog(default_project_paths().repository_root).load()
        plan = plan_selection(catalog, ('swagger',))
        base = adoption_fixture(catalog)
        components = tuple(item for service in catalog.services if service.service_id in plan.resolved_services for item in service.components)
        selected = base.model_copy(update={'requested_services': plan.requested_services,
            'resolved_services': plan.resolved_services, 'selection_reasons': plan.selection_reasons,
            'service_preset': plan.service_preset, 'components': components})
        migrated = migrate_manifest_v1(selected)
        catalog.validate_manifest(migrated)
        self.assertEqual(migrated.service_exposure, {'swagger': 'published'})
        assert migrated.stack_ownership is not None
        self.assertEqual(migrated.stack_ownership['swagger'].owner, 'swarm')
        supplied = {'owner': 'portainer', 'endpoint_id': 1, 'stack_id': 2, 'resource_control_id': 3,
                    'ownership_fingerprint': 'sha256:' + 'c' * 64, 'definition_fingerprint': 'sha256:' + 'd' * 64}
        owner = PortainerOwnership.model_validate(supplied)
        payload = migrated.model_dump()
        payload.update(service_exposure={'swagger': 'internal'}, stack_ownership={'swagger': owner})
        internal = InstallationManifest.model_validate(payload)
        self.assertEqual(decode_manifest(internal.model_dump_json().encode()), internal)
        for field in ('endpoint_id', 'stack_id', 'resource_control_id'):
            for invalid in (False, 0, -1, '1'):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValidationError):
                    PortainerOwnership.model_validate({**supplied, field: invalid})
        for field in ('ownership_fingerprint', 'definition_fingerprint'):
            with self.assertRaises(ValidationError):
                PortainerOwnership.model_validate({**supplied, field: 'same-name-stack'})

    def test_profile_tuple_identity_and_immutable_intent_are_not_ambient_recomputed(self):
        from tiny_swarm_world.domain.lifecycle.models import (
            InstallationProfileBinding, InstallationProfileIntent, ProxyRoute,
            installation_profile_name, migrate_manifest_v1,
        )
        manifest = migrate_manifest_v1(manifest_fixture())
        route = ProxyRoute(device_name='tsw-proxy-10001', listen_address='0.0.0.0',
                           listen_port=10001, connect_port=10001)
        binding = InstallationProfileBinding(profile_name=installation_profile_name(manifest.installation_id), routes=(route,))
        payload = manifest.model_dump()
        payload['installation_profile'] = binding
        manifest = InstallationManifest.model_validate(payload)
        intent = InstallationProfileIntent(operation_id='a' * 32, operation_kind='setup',
            installation_id=manifest.installation_id, controller_revision='b' * 40,
            product_source_revision=manifest.product.revision, product_target_revision=None,
            incus_version='6.0.5', manifest_token=None, requested_services=manifest.requested_services,
            resolved_services=manifest.resolved_services, service_exposure={}, stack_ownership={}, profile=binding)
        intent.validate_manifest(manifest)
        restored = InstallationProfileIntent.model_validate_json(intent.model_dump_json())
        self.assertEqual(restored, intent)
        for field, invalid in (('profile_name', 'same-name'), ('project', 'other')):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                InstallationManifest.model_validate({**payload, 'installation_profile': {**binding.model_dump(), field: invalid}})
        malformed_routes: tuple[dict[str, object], ...] = ({'listen_port': True}, {'nat': 0},
            {'proxy_protocol': 0}, {'unknown_option': 'on'}, {'bind': 'guest'}, {'listen_protocol': 'udp'})
        for changes in malformed_routes:
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                ProxyRoute.model_validate({**route.model_dump(), **changes})
        with self.assertRaises(ValidationError):
            InstallationProfileBinding(profile_name=binding.profile_name, routes=(route, route))
        changed = manifest.model_copy(update={'installation_id': str(uuid4())})
        with self.assertRaises(ValueError):
            restored.validate_manifest(changed)
