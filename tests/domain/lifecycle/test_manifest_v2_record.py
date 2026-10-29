"""Unadopted V2 draft strictness and policy recomputation tests."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from typing import cast
import unittest

from tests.domain.lifecycle.test_scoped_route_policy import make_fixture
from tiny_swarm_world.domain.lifecycle.manifest_v2_record import (
    UnadoptedV2Record, create_v2_record, encode_v2_record, validate_v2_wire,
)
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode


class V2RecordTests(unittest.TestCase):
    def test_minimal_roundtrip_preserves_v1_and_has_unknown_provenance(self) -> None:
        manifest, catalog = make_fixture()
        record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                  listen_address="127.0.0.1")
        payload = record.wire()
        self.assertEqual(payload["v1"], manifest.model_dump(mode="json"))
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["record_state"], "UNADOPTED")
        provenance = cast(dict[str, object], payload["provenance"])
        self.assertEqual(provenance, {"runtime_source": "UNKNOWN", "host": "UNKNOWN", "project": "UNKNOWN",
                                      "profile": "UNKNOWN", "routes": "UNKNOWN", "owner": "UNKNOWN",
                                      "applied": False, "qualified": False})
        loaded = validate_v2_wire(json.loads(encode_v2_record(record)), catalog,
                                  exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
        self.assertEqual(encode_v2_record(loaded), encode_v2_record(record))
        self.assertNotIn("TSW_PORTAINER", repr(record))
        self.assertNotIn("12345678", str(record))

    def test_p1_affected_selections_roundtrip_without_adoption(self) -> None:
        for selected, has_8086 in ((("infisical",), False),
                                   (("service-access", "nexus", "infisical", "traefik"), True)):
            with self.subTest(selected=selected):
                manifest, catalog = make_fixture(selected, "service-access")
                record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                          listen_address="127.0.0.1")
                wire = record.wire()
                desired = cast(dict[str, object], wire["desired"])
                routes = cast(list[dict[str, object]], desired["routes"])
                self.assertIn(17080, [row["listen_port"] for row in routes])
                matches = [row for row in routes if row["listen_port"] == 8086]
                self.assertEqual(bool(matches), has_8086)
                if matches:
                    self.assertEqual(matches[0]["service_id"], "service-access")
                self.assertEqual(validate_v2_wire(wire, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                                  listen_address="127.0.0.1").wire(), wire)

    def test_mutable_input_and_wire_copy_cannot_change_record(self) -> None:
        manifest, catalog = make_fixture(("nexus",))
        record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                  listen_address="127.0.0.1")
        before = encode_v2_record(record)
        wire = record.wire()
        cast(dict[str, object], wire["v1"])["host"] = "wsl2"
        manifest.selection_reasons["portainer"] = ("nexus",)
        self.assertEqual(encode_v2_record(record), before)
        with self.assertRaises(TypeError):
            record._wire["record_state"] = "ADMITTED"  # type: ignore[index]
        with self.assertRaises(FrozenInstanceError):
            record._wire = {}  # type: ignore[misc]
        with self.assertRaises(TypeError):
            UnadoptedV2Record()

    def test_unknown_extra_wrong_types_and_untrusted_desired_fail(self) -> None:
        manifest, catalog = make_fixture()
        record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                  listen_address="127.0.0.1")
        for target, key, value in (
            ("root", "schema_version", True), ("root", "extra", "SECRET"),
            ("root", "record_state", "ADMITTED"), ("desired", "project", "SECRET"),
            ("desired", "policy_version", "scoped-route-policy-v1"),
            ("desired", "listen_address", "0.0.0.0"), ("provenance", "owner", "SECRET"),
            ("provenance", "applied", 0),
        ):
            with self.subTest(target=target, key=key):
                wire = record.wire()
                section = wire if target == "root" else cast(dict[str, object], wire[target])
                section[key] = value
                with self.assertRaises(ValueError) as caught:
                    validate_v2_wire(wire, catalog, exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
                self.assertNotIn("SECRET", str(caught.exception))
        with self.assertRaises(ValueError):
            validate_v2_wire(record.wire(), catalog, exposure=SwaggerMode.NOT_APPLICABLE, listen_address="0.0.0.0")

    def test_forged_and_gap_inputs_cannot_create_record(self) -> None:
        manifest, catalog = make_fixture(("swagger",))
        for exposure in (SwaggerMode.INTERNAL, SwaggerMode.UNKNOWN, cast(SwaggerMode, "published")):
            with self.subTest(exposure=exposure), self.assertRaises(ValueError):
                create_v2_record(manifest, catalog, exposure=exposure, listen_address="127.0.0.1")
        with self.assertRaises(ValueError):
            create_v2_record(manifest.model_copy(update={"schema_version": True}), catalog,
                             exposure=SwaggerMode.PUBLISHED, listen_address="127.0.0.1")


if __name__ == "__main__":
    unittest.main()
