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
