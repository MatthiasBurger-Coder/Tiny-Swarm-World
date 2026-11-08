#!/usr/bin/env python3
"""Read-only WSL guest preservation proof; never a native-host qualification."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import native_runtime_inventory as native
else:
    native = importlib.import_module((__package__ + "." if __package__ else "") + "native_runtime_inventory")

COLLECTOR_SHA = "e25e66fce5636bb778a53fb649b0dee414be21c299586769a19d140ea5ac8856"
PROVENANCE_SHA = "96213743fdfaa31a9e75690b5e49a975167f9f7025862b71611633ef894da9d9"
DETAIL_KINDS = {"project_show", "profile_show", "instance_config_show", "instance_config_show_expanded", "network_show",
                "storage_show", "storage_volume_show", "storage_snapshot_show", "image_show", "image_cache_show"}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def assert_restart_safe(metadata: dict[str, Any]) -> None:
    """Refuse existing autostart effects; never alter an instance/profile."""
    if metadata.get("status") != "Stopped" or type(metadata.get("status_code")) is not int or metadata["status_code"] != 102:
        raise native.InventoryError("GUEST_DETAIL_NOT_STOPPED")
    config = metadata.get("expanded_config", {})
    if not isinstance(config, dict):
        raise native.InventoryError("GUEST_AUTOSTART_UNSAFE")
    auto = config.get("boot.autostart", "")
    if not isinstance(auto, str) or auto not in {"", "false"}:
        raise native.InventoryError("GUEST_AUTOSTART_UNSAFE")
    if "volatile.last_state.power" in config and not isinstance(config["volatile.last_state.power"], str):
        raise native.InventoryError("GUEST_AUTOSTART_UNSAFE")
    if auto == "" and config.get("volatile.last_state.power", "STOPPED") != "STOPPED":
        raise native.InventoryError("GUEST_AUTOSTART_UNSAFE")


class DetailObserver(native.Runner):
    """Forward the unchanged runner; retain only stable detail digests in RAM."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.details: dict[tuple[str, ...], str] = {}

    def run(self, argv: list[str], *, env: dict[str, str] | None = None,
            command_id: str, safe_args: list[str] | None = None,
            expected: set[int] = {0}) -> tuple[int, bytes, bytes]:
        result = super().run(argv, env=env, command_id=command_id,
                             safe_args=safe_args, expected=expected)
        kind = command_id.partition("_")[2]
        if kind in DETAIL_KINDS:
            response = native.strict_json(result[1])
            if not isinstance(response, dict) or not isinstance(response.get("metadata"), dict):
                raise native.InventoryError("GUEST_DETAIL_INVALID")
            metadata = response["metadata"]
            # The existing collector validates complete DTOs and all relations
            # before this observation may be returned. Preserve config, device,
            # UUID, descriptions and field presence without exporting values.
            if kind in {"instance_config_show", "instance_config_show_expanded"}:
                assert_restart_safe(metadata)
                metadata = {key: value for key, value in metadata.items()
                            if key not in {"status", "status_code", "last_used_at"}}
            if kind == "image_show":
                metadata = {key: value for key, value in metadata.items() if key != "last_used_at"}
            key = (command_id, *(safe_args or []))
            observed = digest(metadata)
            if key in self.details and self.details[key] != observed:
                raise native.InventoryError("GUEST_DETAIL_DRIFT")
            self.details[key] = observed
        return result


def project(artifact: dict[str, Any], details: dict[tuple[str, ...], str]) -> dict[str, Any]:
    """Structural reuse only: native target/PIDs/timestamps are not WSL identity."""
    if type(artifact.get("schema_version")) is not int or artifact["schema_version"] != 6:
        raise native.InventoryError("GUEST_IMAGE_AWARE_SCHEMA_REQUIRED")
    native._validate_artifact(artifact)
    graph = {family: {"admission": artifact[family + "_admission"],
                      "pools": artifact[family + "_pools"],
                      "projects": artifact[family + "_projects"],
                      "units": [{key: value for key, value in row.items() if key != "main_pid"}
                                for row in artifact[family + "_units"]],
                      "executables": [{key: value for key, value in row.items() if key != "main_pid"}
                                      for row in artifact[family + "_executables"]]}
             for family in ("lxd", "incus")}
    instances = [instance for family in graph.values() for row in family["projects"]
                 for instance in row["instances"]]
    if any(instance["status"] != "Stopped" for instance in instances):
        raise native.InventoryError("GUEST_RUNNING_INSTANCE_BLOCKED")
    expected = {(row["command_id"], *row["safe_args"])
                for row in artifact["command_records"]
                if row["command_id"].partition("_")[2] in DETAIL_KINDS}
    if expected != set(details) or any(not re.fullmatch(r"[0-9a-f]{64}", value)
                                       for value in details.values()):
        raise native.InventoryError("GUEST_DETAIL_PROOF_INCOMPLETE")
    return {"schema_version": 1, "scope": "WSL_GUEST_PRESERVATION_ONLY",
            "decision": "ALL_INSTANCES_STOPPED_GRAPH_COMPLETE",
            "source_commit": artifact["source_commit"],
            "graph_sha256": digest(graph),
            "detail_sha256": digest([[list(key), details[key]] for key in sorted(details)]),
            "instance_count": len(instances),
            "project_count": sum(len(family["projects"]) for family in graph.values()),
            "detail_count": len(details), "command_count": len(artifact["command_records"])}


def assert_source() -> str:
    """Require a root-private source tree and exact reviewed collector/helper."""
    source = Path(__file__).absolute()
    for path in (source, *source.parents):
        row = path.lstat()
        if row.st_uid != 0 or row.st_mode & 0o022 or stat.S_ISLNK(row.st_mode):
            raise native.InventoryError("GUEST_SOURCE_UNTRUSTED")
    for filename, expected in (("native_runtime_inventory.py", COLLECTOR_SHA),
                               ("native_lxd_snap_provenance.py", PROVENANCE_SHA)):
        path = source.with_name(filename)
        row = path.lstat()
        if (not stat.S_ISREG(row.st_mode) or row.st_uid != 0 or row.st_mode & 0o022
                or row.st_size > 1024 * 1024
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise native.InventoryError("GUEST_SOURCE_UNTRUSTED")
    return hashlib.sha256(source.read_bytes()).hexdigest()


def capture(source_commit: str) -> dict[str, Any]:
    if os.geteuid() != 0 or "microsoft" not in Path("/proc/sys/kernel/osrelease").read_text().lower():
        raise native.InventoryError("GUEST_WSL_ROOT_REQUIRED")
    source_before = assert_source()
    observer = DetailObserver()
    # The native artifact exists only in RAM for structural validation. Its
    # static target is never exported or used to prove Windows/registration
    # identity. The Windows controller supplies that independent binding.
    artifact = native.capture(source_commit, runner=observer, image_aware=True)
    result = project(artifact, observer.details)
    if assert_source() != source_before:
        raise native.InventoryError("GUEST_SOURCE_DRIFT")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    arguments = parser.parse_args(argv)
    try:
        result = capture(arguments.source_commit)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (native.InventoryError, OSError, ValueError, TypeError):
        # No native exception message, raw DTO, process, path or address output.
        print('{"schema_version":1,"scope":"WSL_GUEST_PRESERVATION_ONLY","decision":"BLOCKED"}')
        return 2


if __name__ == "__main__":
    sys.exit(main())
