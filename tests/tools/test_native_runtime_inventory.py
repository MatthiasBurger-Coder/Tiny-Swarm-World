"""Regression tests for the fail-closed native runtime inventory."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from tools.linux.qualification import native_runtime_inventory as inventory


class NativeRuntimeInventoryTests(unittest.TestCase):
    class _InventoryRunner(inventory.Runner):
        def __init__(self):
            self.calls: list[tuple[list[str], dict[str, str], str]] = []
            self.records: list[dict[str, Any]] = []
            self.version_output = b"Client version: 6.0\nServer version: 6.0.5\n"
            self.list_rows: dict[str, list[dict[str, Any]]] = {}
            self.project_config = {"features.networks": "true", "features.profiles": "true", "features.storage.volumes": "true"}
            self.detail_profiles = ["bravo"]
            self.instance_network = "net"
            self.instance_pool = "pool"
            self.instance_custom_source: str | None = None
            self.project_used_by: list[str] = [
                "/1.0/profiles/bravo?project=alpha", "/1.0/profiles/zeta?project=alpha",
                "/1.0/instances/web?project=alpha", "/1.0/networks/net?project=alpha",
                "/1.0/storage-pools/pool/volumes/container/web?project=alpha",
            ]
            self.network_used_by = ["/1.0/profiles/bravo?project=alpha", "/1.0/instances/web?project=alpha"]
            self.volume_used_by = ["/1.0/instances/web?project=alpha"]
            self.pool_used_by = ["/1.0/profiles/bravo?project=alpha", "/1.0/instances/web?project=alpha"]
            self.volume_owner_project = "alpha"
            self.volume_list_pool: object = "pool"
            self.volume_detail_pool: object = "pool"
            self.omit_volume_list_pool = False
            self.omit_volume_detail_pool = False
            self.detail_overrides: dict[str, dict[str, Any]] = {}
            self.omit_default_project = False

        @staticmethod
        def _json(value: Any) -> bytes:
            import json
            return json.dumps(value).encode()

        def server_row(self, incus):
            displayed = next(line.split(":", 1)[1].strip() for line in self.version_output.decode().splitlines() if line.startswith("Server version:"))
            version = displayed[:-4] if not incus and displayed.endswith(" LTS") else displayed
            environment = {key: "" for key in (
                "certificate", "certificate_fingerprint", "driver", "driver_version", "firewall", "kernel",
                "kernel_architecture", "kernel_version", "os_name", "os_version", "project", "server",
                "server_event_mode", "server_name", "server_version", "storage", "storage_version")}
            environment.update(project="default", server="incus" if incus else "lxd", server_version=version,
                               server_clustered=False, server_pid=999, addresses=[], architectures=[],
                               kernel_features={}, lxc_features={}, storage_supported_drivers=[{"Name": "dir", "Version": "1", "Remote": False}])
            metadata = {"api_status": "stable", "api_version": "1.0", "auth": "trusted", "public": False,
                        "auth_user_name": "", "auth_user_method": "unix", "api_extensions": [],
                        "auth_methods": [], "config": {}, "environment": environment}
            if not incus:
                metadata["client_certificate"] = False
                environment.update(backup_metadata_version_range=[1, 2], instance_types=["container", "virtual-machine"],
                                   server_lts=displayed.endswith(" LTS"))
            return metadata

        def run(self, argv: list[str], *, env: dict[str, str] | None = None, command_id: str,
                safe_args: list[str] | None = None, expected: set[int] | None = None) -> tuple[int, bytes, bytes]:
            self.calls.append((list(argv), dict(env or {}), command_id))
            suffix = argv[2:]
            if suffix == ["version"]:
                out = self.version_output
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0"]:
                out = self._json(self.server_row(argv[0] == "/usr/bin/incus"))
            elif suffix == ["project", "list", "--format", "json"]:
                listed_projects = self.list_rows.get("projects", [{"name": "alpha", "description": "", "config": self.project_config,
                                                                    "used_by": self.project_used_by}])
                if not self.omit_default_project:
                    listed_projects = listed_projects + [{"name": "default", "config": {}, "used_by": []}]
                out = self._json(listed_projects)
            elif "default" in suffix and suffix[0] in {"profile", "network"}:
                out = self._json([])
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/projects/default?project=default"]:
                out = self._json({"name": "default", "config": {}, "used_by": []})
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/instances?project=default&recursion=1"]:
                out = self._json([])
            elif suffix == ["storage", "list", "--project", "default", "--format", "json"]:
                out = self._json([{ "name": "pool", "driver": "dir", "config": {}, "description": "", "status": "Created", "locations": self.list_rows.get("pools", [{}])[0].get("locations", []), "used_by": self.pool_used_by}])
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool?project=default"]:
                out = self._json({"name": "pool", "driver": "dir", "config": {}, "description": "", "status": "Created", "locations": [], "used_by": self.pool_used_by})
            elif suffix == ["storage", "volume", "list", "pool", "--project", "default", "--format", "json"]:
                out = self._json([])
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/projects/alpha?project=alpha"]:
                out = self._json({"name": "alpha", "config": self.project_config, "used_by": self.project_used_by})
            elif suffix == ["profile", "list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("profiles", [
                    {"name": "zeta", "project": "alpha", "description": "", "config": {}, "devices": {}, "used_by": []},
                    {"name": "bravo", "project": "alpha", "description": "", "config": {},
                     "devices": {"root": {"type": "disk", "path": "/", "pool": "pool"}, "eth0": {"type": "nic", "network": "net"}},
                     "used_by": ["/1.0/instances/web?project=alpha"]},
                ]))
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/instances?project=alpha&recursion=1"]:
                out = self._json(self.list_rows.get("instances", [{
                    "name": "web", "project": "alpha", "architecture": "x86_64", "config": {}, "devices": {},
                    "ephemeral": False, "expanded_config": {}, "expanded_devices": {}, "profiles": ["bravo"],
                    "stateful": False, "status": "Running", "status_code": 103, "type": "container",
                    "location": "none", "description": "", "created_at": "2026-10-01T00:00:00Z",
                    "last_used_at": "2026-10-02T00:00:00Z",
                }]))
            elif suffix == ["network", "list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("networks", [{"name": "net", "project": "alpha", "type": "bridge",
                    "managed": True, "status": "Created", "config": {}, "description": "",
                    "used_by": self.network_used_by, "locations": []}]))
            elif suffix == ["storage", "list", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("pools", [{"name": "pool", "project": "alpha", "driver": "dir",
                    "config": {}, "description": "", "used_by": self.pool_used_by,
                    "status": "Created", "locations": []}]))
            elif suffix in (
                    ["query", "--request", "GET", "--raw", "/1.0/profiles/bravo?project=alpha"],
                    ["query", "--request", "GET", "--raw", "/1.0/profiles/zeta?project=alpha"]):
                profile_name = "bravo" if suffix[-1] == "/1.0/profiles/bravo?project=alpha" else "zeta"
                profile = {"name": profile_name, "project": "alpha", "description": "", "config": {},
                           "devices": ({"root": {"type": "disk", "path": "/", "pool": "pool"},
                                        "eth0": {"type": "nic", "network": "net"}}
                                       if profile_name == "bravo" else {}),
                           "used_by": ["/1.0/instances/web?project=alpha"] if profile_name == "bravo" else []}
                out = self._json(profile)
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/instances/web?project=alpha"]:
                devices = {}
                if self.instance_custom_source is not None:
                    devices["custom"] = {"type": "disk", "path": "/data", "pool": self.instance_pool,
                                         "source": self.instance_custom_source}
                out = self._json({"name": "web", "project": "alpha", "config": {}, "devices": devices,
                                  "expanded_config": {"security.nesting": "true"},
                                  "expanded_devices": {"root": {"type": "disk", "path": "/", "pool": self.instance_pool},
                                                       "eth0": {"type": "nic", "network": self.instance_network}, **devices},
                                  "ephemeral": False, "profiles": self.detail_profiles, "stateful": False,
                                  "architecture": "x86_64", "description": "", "created_at": "2026-10-01T00:00:00Z",
                                  "last_used_at": "2026-10-02T00:00:00Z", "status": "Running", "status_code": 103,
                                  "type": "container", "location": "none"})
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/networks/net?project=alpha"]:
                out = self._json({"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                                  "config": {}, "used_by": self.network_used_by})
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool?project=alpha"]:
                out = self._json({"name": "pool", "project": "alpha", "driver": "dir", "config": {},
                                  "description": "", "status": "Created", "locations": [], "used_by": self.pool_used_by})
            elif suffix == ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"]:
                out = self._json(self.list_rows.get("volumes", [{"name": "web", "type": "container",
                    "content_type": "filesystem", "project": "alpha", "description": "", "config": {"size": "10GiB"},
                    "created_at": "2026-10-01T00:00:00Z", "used_by": self.volume_used_by, "location": "none"}]))
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool/volumes/container/web?project=alpha"]:
                out = self._json({"name": "web", "type": "container", "content_type": "filesystem",
                                  "project": self.volume_owner_project, "description": "", "config": {"size": "10GiB"},
                                  "created_at": "2026-10-01T00:00:00Z", "used_by": self.volume_used_by, "location": "none"})
            else:
                raise AssertionError(f"unexpected inventory argv: {argv}")
            if argv[0] != "/usr/bin/incus" and suffix[:3] == ["storage", "volume", "list"]:
                volume_list = json.loads(out)
                for listed_volume in volume_list:
                    if not self.omit_volume_list_pool:
                        listed_volume["pool"] = self.volume_list_pool
                out = self._json(volume_list)
            if suffix[0] == "query":
                metadata = json.loads(out)
                if isinstance(metadata, dict):
                    if argv[0] != "/usr/bin/incus" and command_id == "lxd_storage_volume_show" and not self.omit_volume_detail_pool:
                        metadata["pool"] = self.volume_detail_pool
                    metadata.update(self.detail_overrides.get(command_id, {}))
                out = self._json({"type": "sync", "status": "Success", "status_code": 200,
                                  "operation": "", "error_code": 0, "error": "", "metadata": metadata})
            self.records.append({"command_id": command_id, "safe_args": safe_args or [], "exit_status": 0,
                                 "stdout_bytes": len(out), "stderr_bytes": 0})
            return 0, out, b""

    class _NetworkRunner(_InventoryRunner):
        def __init__(self):
            super().__init__()
            self.configs = {"alpha": {"features.profiles": "true", "features.networks": "false"}, "default": {}}
            self.profile_devices = {"alpha": {"eth0": {"type": "nic", "network": "net"}}, "default": {}}
            self.expanded_devices = {"alpha": {"eth0": {"type": "nic", "network": "net"}}, "default": {}}
            self.local_devices: dict[str, dict[str, dict[str, str]]] = {"alpha": {}, "default": {}}
            self.networks = {
                "alpha": [self.network("eth0", False, "physical"), self.network("lo", False, "loopback"), self.network("net", True)],
                "default": [self.network("eth0", False, "physical"), self.network("lo", False, "loopback"), self.network("net", True)],
            }
            self.network_users = {"eth0": [], "lo": [], "net": ["/1.0/profiles/profile?project=alpha", "/1.0/instances/web?project=alpha"]}
            self.list_mutation: Any = lambda _project, _rows: None
            self.detail_mutation: Any = lambda _project, _kind, _row: None
            self.project_links: Any = None
            self.project_override: Any = None
            self.default_profile = False
            self.instance_projects = {"alpha"}
            self.root_pools = {"alpha": "pool", "default": "pool"}
            self.storage_pools = ["pool"]
            self.storage_volumes = {("alpha", "pool"): [{"name": "web", "type": "container", "project": "alpha",
                "config": {}, "content_type": "filesystem", "location": "none", "used_by": ["/1.0/instances/web?project=alpha"]}]}
            self.pool_users_override: dict[str, list[str]] = {}
            self.hidden_pool_projects: set[str] = set()

        @staticmethod
        def network(name, managed, kind="bridge"):
            return {"name": name, "type": kind, "managed": managed,
                    "status": "Created" if managed else "", "config": {}, "used_by": [], "locations": None}

        def run(self, argv, *, env=None, command_id, safe_args=None, expected=None):
            from urllib.parse import parse_qs, urlsplit
            suffix = argv[2:]
            if suffix == ["version"]:
                value = b"Client version: 6.0\nServer version: 6.0.5\n"
            elif suffix == ["query", "--request", "GET", "--raw", "/1.0"]:
                return super().run(argv, env=env, command_id=command_id, safe_args=safe_args, expected=expected)
            else:
                project = ""
                if suffix[:2] == ["project", "list"]:
                    value = [self.project_row(name) for name in self.configs]
                elif suffix[0] == "query":
                    uri = urlsplit(suffix[-1])
                    query = parse_qs(uri.query)
                    project = query["project"][0]
                    parts = uri.path.split("/")[2:]
                    kind, name = parts[0], parts[1] if len(parts) > 1 else ""
                    if kind == "projects":
                        value = self.project_row(project)
                    elif kind == "instances" and not name:
                        value = [self.instance_row(project)] if project in self.instance_projects else []
                    elif kind == "instances":
                        value = self.instance_row(project)
                    elif kind == "profiles":
                        value = next(row for row in self.profile_rows(project) if row["name"] == name)
                    elif kind == "storage-pools":
                        if "volumes" in parts:
                            value = copy.deepcopy(next(volume for volume in self.volume_rows(project, name)
                                                       if volume["type"] == parts[3] and volume["name"] == parts[4]))
                            if argv[0] != "/usr/bin/incus":
                                value["pool"] = name
                        else:
                            value = self.pool_row(name)
                    elif kind == "networks":
                        value = copy.deepcopy(next(row for row in self.networks[project] if row["name"] == name))
                        value["used_by"] = list(self.network_users.get(name, []))
                        value["project"] = self.dto_project(argv, project)
                    else:
                        raise AssertionError(argv)
                    if isinstance(value, dict):
                        self.detail_mutation(project, kind, value)
                    value = {"type": "sync", "status": "Success", "status_code": 200,
                             "operation": "", "error_code": 0, "error": "", "metadata": value}
                else:
                    project = suffix[suffix.index("--project") + 1]
                    if suffix[0] == "network":
                        value = copy.deepcopy(self.networks[project])
                        for row in value:
                            row["used_by"] = list(self.network_users.get(row["name"], []))
                            row["project"] = self.dto_project(argv, project)
                        self.list_mutation(project, value)
                    elif suffix[0] == "profile":
                        value = self.profile_rows(project)
                    elif suffix[:3] == ["storage", "volume", "list"]:
                        value = self.volume_rows(project, suffix[3])
                        if argv[0] != "/usr/bin/incus":
                            for volume in value:
                                volume["pool"] = suffix[3]
                    elif suffix[0] == "storage":
                        value = [] if project in self.hidden_pool_projects else [self.pool_row(pool_name) for pool_name in self.storage_pools]
                    else:
                        raise AssertionError(argv)
                value = self._json(value)
            self.calls.append((list(argv), dict(env or {}), command_id))
            self.records.append({"command_id": command_id, "safe_args": safe_args or [], "exit_status": 0,
                                 "stdout_bytes": len(value), "stderr_bytes": 0})
            return 0, value, b""

        def dto_project(self, argv, project):
            if self.project_override is not None:
                return self.project_override(argv, project)
            own = self.configs[project].get("features.networks") == "true"
            return project if argv[0] != "/usr/bin/incus" or own else "default"

        def project_row(self, project):
            links = []
            suffix = "" if project == "default" else "?project=" + project
            if project == "alpha" or self.default_profile:
                links.append("/1.0/profiles/profile" + suffix)
            if project in self.instance_projects:
                links.append("/1.0/instances/web" + suffix)
            for (owner, pool), volumes in self.storage_volumes.items():
                if owner == project:
                    links.extend("/1.0/storage-pools/" + pool + "/volumes/" + volume["type"] + "/" + volume["name"] + suffix for volume in volumes)
            for network in self.networks[project]:
                if network["managed"] and (project == "default" or self.configs[project].get("features.networks") == "true"):
                    links.append("/1.0/networks/" + network["name"] + suffix)
            if self.project_links is not None:
                links = self.project_links(project, links)
            return {"name": project, "config": self.configs[project], "used_by": links}

        def profile_rows(self, project):
            return [self.profile_row(project)] if project == "alpha" or self.default_profile else []

        def profile_row(self, project):
            return {"name": "profile", "project": project, "config": {}, "devices": {"root": {"type": "disk", "path": "/", "pool": self.root_pools[project]}, **self.profile_devices[project]},
                    "used_by": ["/1.0/instances/web" + ("" if project == "default" else "?project=" + project)] if project in self.instance_projects else []}

        def instance_row(self, project):
            return {"name": "web", "project": project, "config": {}, "devices": self.local_devices[project],
                    "expanded_config": {}, "expanded_devices": {"root": {"type": "disk", "path": "/", "pool": self.root_pools[project]}, **self.expanded_devices[project]},
                    "profiles": ["profile"], "ephemeral": False, "stateful": False,
                    "status": "Running", "type": "container", "location": "none"}

        def pool_row(self, pool_name):
            users = []
            for project in self.configs:
                suffix = "" if project == "default" else "?project=" + project
                if project == "alpha" or self.default_profile:
                    if any(device.get("type") == "disk" and device.get("pool") == pool_name for device in self.profile_row(project)["devices"].values()):
                        users.append("/1.0/profiles/profile" + suffix)
                for volume in self.volume_rows(project, pool_name):
                    path = "/1.0/instances/" + volume["name"] if volume["type"] in {"container", "virtual-machine"} else "/1.0/storage-pools/" + pool_name + "/volumes/" + volume["type"] + "/" + volume["name"]
                    users.append(path + suffix)
            return {"name": pool_name, "driver": "dir", "config": {}, "description": "", "status": "Created",
                    "locations": [], "used_by": self.pool_users_override.get(pool_name, users)}

        def volume_rows(self, project, pool):
            return copy.deepcopy(self.storage_volumes.get((project, pool), []))

    class _InheritedProfileRunner(_NetworkRunner):
        def __init__(self):
            super().__init__()
            self.configs["alpha"]["features.profiles"] = "false"
            self.default_profile = True
            self.profile_names = ["profile"]
            self.profile_order = {"alpha": ["profile"], "default": ["profile"]}
            self.profile_view_changes: dict[str, dict[str, Any]] = {}
            self.profile_list_changes: dict[str, dict[str, Any]] = {}
            self.missing_profile_views: set[str] = set()
            self.extra_profile_views: set[str] = set()
            self.profile_devices["default"] = copy.deepcopy(self.profile_devices["alpha"])
            self.network_users["net"] = ["/1.0/profiles/profile", "/1.0/instances/web?project=alpha"]

        def profile_owner(self, project):
            return project if self.configs[project].get("features.profiles") == "true" else "default"

        def profile_rows(self, project):
            if project in self.missing_profile_views:
                return []
            owner = self.profile_owner(project)
            rows = []
            names = self.profile_names + (["extra"] if project in self.extra_profile_views else [])
            for name in names:
                used_by = ["/1.0/instances/web" + ("" if user == "default" else "?project=" + user)
                           for user in self.instance_projects
                           if self.profile_owner(user) == owner and name in self.profile_order[user]]
                devices = ({"root": {"type": "disk", "path": "/", "pool": self.root_pools[owner]},
                            **self.profile_devices[owner]}) if name == "profile" else {}
                row = {"name": name, "project": owner, "description": "profile metadata", "config": {},
                       "devices": copy.deepcopy(devices), "used_by": used_by}
                row.update(copy.deepcopy(self.profile_view_changes.get(project, {})))
                rows.append(row)
            return rows

        def profile_row(self, project):
            return self.profile_rows(project)[0]

        def instance_row(self, project):
            return {**super().instance_row(project), "profiles": list(self.profile_order[project])}

        def project_row(self, project):
            row = super().project_row(project)
            row["used_by"] = [link for link in row["used_by"] if not link.startswith("/1.0/profiles/")]
            if self.profile_owner(project) == project:
                suffix = "" if project == "default" else "?project=" + project
                row["used_by"].extend("/1.0/profiles/" + name + suffix for name in self.profile_names)
            return row

        def pool_row(self, pool_name):
            users = []
            for (owner, pool), volumes in self.storage_volumes.items():
                if pool != pool_name:
                    continue
                suffix = "" if owner == "default" else "?project=" + owner
                for volume in volumes:
                    path = "/1.0/instances/" + volume["name"] if volume["type"] in {"container", "virtual-machine"} else "/1.0/storage-pools/" + pool_name + "/volumes/" + volume["type"] + "/" + volume["name"]
                    users.append(path + suffix)
            for owner in {self.profile_owner(project) for project in self.configs}:
                devices = {"root": {"type": "disk", "path": "/", "pool": self.root_pools[owner]}, **self.profile_devices[owner]}
                if "profile" in self.profile_names and any(device.get("type") == "disk" and device.get("pool") == pool_name for device in devices.values()):
                    users.append("/1.0/profiles/profile" + ("" if owner == "default" else "?project=" + owner))
            return {"name": pool_name, "driver": "dir", "config": {}, "description": "", "status": "Created",
                    "locations": [], "used_by": self.pool_users_override.get(pool_name, users)}

        def run(self, argv, **kwargs):
            status, raw, err = super().run(argv, **kwargs)
            if argv[2:4] == ["profile", "list"]:
                project = argv[argv.index("--project") + 1]
                profiles = json.loads(raw)
                for row in profiles:
                    row.update(copy.deepcopy(self.profile_list_changes.get(project, {})))
                raw = self._json(profiles)
            return status, raw, err

    def _network_rows(self, runner=None, *, incus=True):
        runner = runner or self._NetworkRunner()
        return inventory._inventory_client(runner, "incus_system" if incus else "lxd_system",
                                           "/run/incus/unix.socket" if incus else "/var/lib/lxd/unix.socket",
                                           incus=incus, before_query=lambda: None)[1]

    def _network_artifact(self):
        artifact = self._valid_artifact()
        self._bind_artifact(artifact, self._network_rows(), incus=True)
        return artifact

    def _bind_artifact(self, artifact, rows, *, incus, cli_version="6.0.5"):
        family = "incus" if incus else "lxd"
        unit = "incus.service" if incus else "lxd.service"
        identity = "incus_system" if incus else "lxd_system"
        for state in artifact[family + "_units"]:
            if state["unit"] == unit:
                state.update(load_state="loaded", active_state="active", sub_state="running", unit_file_state="enabled", main_pid=4242)
        artifact[family + "_executables"] = [{"unit": unit, "main_pid": 4242, "identity_id": identity,
                                               "package": "system:" + family, "version": cli_version}]
        artifact[family + "_projects"] = rows
        artifact[family + "_pools"] = inventory._canonical_pools(rows)
        fixture = self._InventoryRunner()
        fixture.version_output = ("Server version: " + cli_version + "\n").encode()
        admission = inventory._validate_server_root(fixture.server_row(incus), incus=incus, cli_version=cli_version)
        artifact[family + "_admission"] = {"initial": admission, "final": dict(admission)}
        artifact["command_records"] = [record for record in artifact["command_records"] if not record["command_id"].startswith(family + "_")]
        artifact["command_records"].extend({"command_id": family + "_" + suffix, "safe_args": [],
                                             "exit_status": 0, "stdout_bytes": 0, "stderr_bytes": 0}
                                            for suffix in ("version", "server_root_initial", "project_list", "server_root_final"))

    class _Selector:
        def __init__(self) -> None:
            self.items: dict[Any, str] = {}

        def register(self, fileobj: Any, _events: int, data: str) -> None:
            self.items[fileobj] = data

        def get_map(self) -> dict[Any, str]:
            return self.items

        def select(self, _timeout: float) -> list[tuple[Any, int]]:
            return [(type("Key", (), {"fileobj": obj, "fd": obj.fileno(), "data": data})(), 1)
                    for obj, data in list(self.items.items())]

        def unregister(self, fileobj: Any) -> None:
            self.items.pop(fileobj)

    @staticmethod
    def _valid_artifact(command_records=None):
        units = []
        for unit in inventory.UNITS:
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive",
                   "sub_state": "dead", "unit_file_state": "", "main_pid": 0}
            if unit.endswith(".socket"):
                row["listen"] = ""
            units.append(row)
        return {"schema_version": 4, "target_host": inventory.TARGET, "source_commit": "a" * 40,
                "captured_at_utc": "2026-01-01T00:00:00Z", "lxd_units": units[:3], "incus_units": units[3:],
                "lxd_executables": [], "incus_executables": [],
                "sockets": [{"endpoint_id": endpoint, "state": "absent", "unit": ""}
                            for endpoint in inventory.SOCKETS.values()],
                "lxd_projects": [], "incus_projects": [], "lxd_pools": [], "incus_pools": [],
                "lxd_admission": None, "incus_admission": None, "command_records": command_records or [],
                "decision": "READ_ONLY_INVENTORY_COMPLETE"}

    class _UnitDiagnosticRunner:
        def __init__(self, unit_rows: dict[str, list[dict[str, Any]]], executable_paths: dict[int, bytes],
                     *, failure: inventory.InventoryError | None = None):
            self.unit_rows = unit_rows
            self.executable_paths = executable_paths
            self.failure = failure
            self.calls: list[list[str]] = []
            self.unit_counts: dict[str, int] = {}

        @staticmethod
        def _raw_unit(row: dict[str, Any]) -> bytes:
            values = {
                "LoadState": row["load_state"], "ActiveState": row["active_state"],
                "SubState": row["sub_state"], "UnitFileState": row["unit_file_state"],
                "MainPID": str(row["main_pid"]),
            }
            if row["unit"].endswith(".socket"):
                values["Listen"] = next((path for path, endpoint in inventory.SOCKETS.items()
                                          if endpoint == row["listen"]), "")
            return "".join(f"{key}={value}\n" for key, value in values.items()).encode()

        def run(self, argv: list[str], *, env: dict[str, str] | None = None, command_id: str,
                safe_args: list[str] | None = None, expected: set[int] | None = None) -> tuple[int, bytes, bytes]:
            self.calls.append(list(argv))
            self.assert_sanitized_runner_inputs(argv, env, command_id, safe_args)
            if argv[0] == "/usr/bin/systemctl":
                unit = argv[2]
                props = list(inventory.PROPERTIES) + (["Listen"] if unit.endswith(".socket") else [])
                expected_argv = ["/usr/bin/systemctl", "show", unit]
                expected_argv += [f"--property={prop}" for prop in props] + ["--no-pager"]
                if argv != expected_argv:
                    raise AssertionError("diagnostic used unexpected systemctl argv")
                count = self.unit_counts.get(unit, 0)
                self.unit_counts[unit] = count + 1
                rows = self.unit_rows[unit]
                return 0, self._raw_unit(rows[min(count, len(rows) - 1)]), b"systemctl stderr sentinel"
            if argv[0] == "/usr/bin/readlink":
                if len(argv) != 3 or argv[1] != "-f" or not argv[2].startswith("/proc/") or not argv[2].endswith("/exe"):
                    raise AssertionError("diagnostic used unexpected readlink argv")
                if self.failure is not None:
                    raise self.failure
                pid = int(argv[2].split("/")[2])
                return 0, self.executable_paths[pid], b"readlink stderr sentinel"
            raise AssertionError("diagnostic invoked an unapproved command")

        @staticmethod
        def assert_sanitized_runner_inputs(argv: list[str], env: dict[str, str] | None, command_id: str,
                                           safe_args: list[str] | None) -> None:
            if env is not None:
                raise AssertionError("diagnostic must use Runner's fixed environment")
            if command_id not in {"systemctl_show_unit", "systemctl_show_socket", "resolve_executable"}:
                raise AssertionError("diagnostic used an unexpected command id")
            if safe_args not in (None, [argv[2]] if argv[0] == "/usr/bin/systemctl" else None):
                raise AssertionError("diagnostic used unexpected safe arguments")

    def test_strict_json_rejects_duplicates_constants_and_invalid_utf8(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff"):
            with self.subTest(raw=raw), self.assertRaises(inventory.InventoryError):
                inventory.strict_json(raw)

    def test_strict_json_accepts_valid_data(self) -> None:
        self.assertEqual(inventory.strict_json(b'{"x":[1,true]}'), {"x": [1, True]})

    def test_service_unit_exact_active_and_inactive_tuples(self) -> None:
        active = {"LoadState": "loaded", "ActiveState": "active", "SubState": "running",
                  "UnitFileState": "enabled", "MainPID": "42"}
        inactive = {**active, "ActiveState": "inactive", "SubState": "dead", "MainPID": "0"}
        self.assertEqual(inventory._unit_state("lxd.service", active)["main_pid"], 42)
        self.assertEqual(inventory._unit_state("lxd.service", inactive)["main_pid"], 0)
        for mutation in ({**active, "MainPID": "0"}, {**active, "SubState": "dead"},
                         {**inactive, "MainPID": "2"}, {**active, "UnitFileState": "unknown"}):
            with self.subTest(mutation=mutation), self.assertRaises(inventory.InventoryError):
                inventory._unit_state("lxd.service", mutation)

    def test_not_found_service_requires_empty_or_not_found_unit_file_state(self) -> None:
        row = {"LoadState": "not-found", "ActiveState": "inactive", "SubState": "dead",
               "UnitFileState": "not-found", "MainPID": "0"}
        self.assertEqual(inventory._unit_state("incus.service", row)["unit_file_state"], "")
        with self.assertRaises(inventory.InventoryError):
            inventory._unit_state("incus.service", {**row, "UnitFileState": "disabled"})

    def test_socket_unit_requires_zero_pid_and_allowlisted_listen(self) -> None:
        row = {"LoadState": "loaded", "ActiveState": "active", "SubState": "listening",
               "UnitFileState": "enabled", "MainPID": "0", "Listen": "/run/incus/unix.socket (Stream)"}
        self.assertEqual(inventory._unit_state("incus.socket", row)["listen"], "incus_run")
        for mutation in ({**row, "MainPID": "5"}, {**row, "Listen": "/tmp/evil.sock"}):
            with self.subTest(mutation=mutation), self.assertRaises(inventory.InventoryError):
                inventory._unit_state("incus.socket", mutation)

    def test_incus_socket_running_is_the_only_running_socket_state(self) -> None:
        row = {"LoadState": "loaded", "ActiveState": "active", "SubState": "running",
               "UnitFileState": "enabled", "MainPID": "0", "Listen": "/run/incus/unix.socket (Stream)"}
        self.assertEqual(inventory._unit_state("incus.socket", row)["sub_state"], "running")
        self.assertEqual(inventory._unit_state("incus.socket", {k: v for k, v in row.items() if k != "MainPID"})[
            "main_pid"], 0)
        for unit in ("snap.lxd.daemon.unix.socket", "other.socket"):
            with self.subTest(unit=unit), self.assertRaises(inventory.InventoryError):
                inventory._unit_state(unit, row)

    def test_systemctl_socket_output_may_omit_only_zero_main_pid(self) -> None:
        base = ("LoadState=loaded\nActiveState=active\nSubState=running\n"
                "UnitFileState=enabled\nListen=/run/incus/unix.socket (Stream)\n")
        runner = Mock()
        runner.run.return_value = (0, base.encode(), b"")
        self.assertEqual(inventory._systemctl_show(runner, "incus.socket")["main_pid"], 0)
        runner.run.return_value = (0, (base + "MainPID=0\n").encode(), b"")
        self.assertEqual(inventory._systemctl_show(runner, "incus.socket")["main_pid"], 0)
        for invalid_pid in ("", "nope", "42", "00", "٠"):
            with self.subTest(pid=invalid_pid):
                runner.run.return_value = (0, (base + f"MainPID={invalid_pid}\n").encode(), b"")
                with self.assertRaises(inventory.InventoryError):
                    inventory._systemctl_show(runner, "incus.socket")
        service_output = ("LoadState=loaded\nActiveState=active\nSubState=running\n"
                          "UnitFileState=enabled\n")
        runner.run.return_value = (0, service_output.encode(), b"")
        with self.assertRaises(inventory.InventoryError):
            inventory._systemctl_show(runner, "incus.service")

    @staticmethod
    def _diagnostic_active_service(unit: str, pid: int) -> dict[str, Any]:
        return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                "unit_file_state": "enabled", "main_pid": pid}

    @staticmethod
    def _diagnostic_missing_unit(unit: str, *, socket: bool = False) -> dict[str, Any]:
        row: dict[str, Any] = {"unit": unit, "load_state": "not-found", "active_state": "inactive",
                               "sub_state": "dead", "unit_file_state": "", "main_pid": 0}
        if socket:
            row["listen"] = ""
        return row

    def _diagnose_unknown_path(self, unit: str, raw_path: bytes) -> tuple[int, str, str, Any]:
        rows = {name: [self._diagnostic_missing_unit(name, socket=name.endswith(".socket"))]
                for name in inventory.UNITS}
        active = self._diagnostic_active_service(unit, 733)
        rows[unit] = [active, active]
        runner = self._UnitDiagnosticRunner(rows, {733: raw_path})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])
        return result, stdout.getvalue(), stderr.getvalue(), runner

    def test_diagnose_units_success_uses_exactly_eleven_commands_and_emits_symbols_only(self) -> None:
        rows = {
            "lxd.service": [self._diagnostic_active_service("lxd.service", 101)],
            "snap.lxd.daemon.service": [self._diagnostic_active_service("snap.lxd.daemon.service", 202)],
            "snap.lxd.daemon.unix.socket": [{"unit": "snap.lxd.daemon.unix.socket", "load_state": "loaded",
                "active_state": "active", "sub_state": "listening", "unit_file_state": "enabled",
                "main_pid": 0, "listen": "lxd_snap"}],
            "incus.service": [self._diagnostic_active_service("incus.service", 303)],
            "incus.socket": [{"unit": "incus.socket", "load_state": "loaded", "active_state": "active",
                "sub_state": "running", "unit_file_state": "enabled", "main_pid": 0, "listen": "incus_run"}],
        }
        runner = self._UnitDiagnosticRunner(rows, {101: b"/usr/lib/lxd/lxd\n",
            202: b"/snap/lxd/12345/bin/lxd\n", 303: b"/usr/libexec/incus/incusd\n"})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                patch.object(inventory, "_endpoint", side_effect=AssertionError("endpoint query is forbidden")), \
                patch.object(inventory, "_inventory_client", side_effect=AssertionError("client query is forbidden")), \
                patch.object(inventory, "_write_private") as write, \
                patch.object(inventory, "capture", side_effect=AssertionError("inventory capture is forbidden")), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])

        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), '{"mode":"diagnose-units","status":"DIAGNOSTIC_COMPLETE","services":[{"unit":"lxd.service","identity":"lxd_system"},{"unit":"snap.lxd.daemon.service","identity":"lxd_snap"},{"unit":"incus.service","identity":"incus_system"}]}\n')
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(runner.calls), 11)
        self.assertEqual(sum(call[0] == "/usr/bin/systemctl" for call in runner.calls), 8)
        self.assertEqual(sum(call[0] == "/usr/bin/readlink" for call in runner.calls), 3)
        self.assertEqual([call[2] for call in runner.calls if call[0] == "/usr/bin/systemctl"],
                         ["lxd.service", "lxd.service", "snap.lxd.daemon.service", "snap.lxd.daemon.service",
                          "snap.lxd.daemon.unix.socket", "incus.service", "incus.service", "incus.socket"])
        self.assertEqual([call for call in runner.calls if call[0] == "/usr/bin/readlink"], [
            ["/usr/bin/readlink", "-f", "/proc/101/exe"],
            ["/usr/bin/readlink", "-f", "/proc/202/exe"],
            ["/usr/bin/readlink", "-f", "/proc/303/exe"],
        ])
        for forbidden in ("101", "202", "303", "/proc/", "/usr/lib", "/snap/lxd", "stderr sentinel"):
            self.assertNotIn(forbidden, stdout.getvalue() + stderr.getvalue())
        write.assert_not_called()

    def test_diagnose_units_unknown_emits_only_first_unit_and_stops_before_later_queries(self) -> None:
        rows = {
            "lxd.service": [self._diagnostic_active_service("lxd.service", 411)],
            "snap.lxd.daemon.service": [self._diagnostic_active_service("snap.lxd.daemon.service", 422)],
            "snap.lxd.daemon.unix.socket": [self._diagnostic_missing_unit("snap.lxd.daemon.unix.socket", socket=True)],
            "incus.service": [self._diagnostic_missing_unit("incus.service")],
            "incus.socket": [self._diagnostic_missing_unit("incus.socket", socket=True)],
        }
        secret_path = b"/private/SENTINEL_EXECUTABLE_PATH\n"
        runner = self._UnitDiagnosticRunner(rows, {411: b"/usr/lib/lxd/lxd\n", 422: secret_path})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                patch.object(inventory, "_endpoint", side_effect=AssertionError("endpoint query is forbidden")), \
                patch.object(inventory, "_inventory_client", side_effect=AssertionError("client query is forbidden")), \
                patch.object(inventory, "_write_private") as write, redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])

        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"snap.lxd.daemon.service","identity":"UNKNOWN","reason":"SNAP_EXECUTABLE_OUTSIDE_ROOT"}\n')
        self.assertEqual(stderr.getvalue(), "")
        systemctl_units = [call[2] for call in runner.calls if call[0] == "/usr/bin/systemctl"]
        self.assertEqual(systemctl_units, ["lxd.service", "lxd.service", "snap.lxd.daemon.service",
                                           "snap.lxd.daemon.service"])
        self.assertEqual([call for call in runner.calls if call[0] == "/usr/bin/readlink"], [
            ["/usr/bin/readlink", "-f", "/proc/411/exe"],
            ["/usr/bin/readlink", "-f", "/proc/422/exe"],
        ])
        for forbidden in ("411", "422", "/proc/", "/usr/lib", "/private/", "SENTINEL_EXECUTABLE_PATH", "stderr sentinel"):
            self.assertNotIn(forbidden, stdout.getvalue() + stderr.getvalue())
        write.assert_not_called()

    def test_diagnose_units_classifies_snap_path_shape_without_disclosing_path(self) -> None:
        result, stdout, stderr, runner = self._diagnose_unknown_path(
            "snap.lxd.daemon.service", b"/snap/lxd/current/bin/SENTINEL_EXECUTABLE\n")
        self.assertEqual(result, 2)
        self.assertEqual(stdout, '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"snap.lxd.daemon.service","identity":"UNKNOWN","reason":"SNAP_ROOT_PATH_MISMATCH"}\n')
        self.assertEqual(stderr, "")
        self.assertEqual(len([call for call in runner.calls if call[0] == "/usr/bin/readlink"]), 1)
        self.assertNotIn("SENTINEL_EXECUTABLE", stdout + stderr)

    def test_diagnose_units_classifies_invalid_snap_paths_as_unclassifiable(self) -> None:
        for raw_path in (b"\n", b"relative/SENTINEL_PATH\n", b"/snap/lxd/invalid\x00SENTINEL_PATH\n"):
            with self.subTest(raw_path=raw_path):
                result, stdout, stderr, runner = self._diagnose_unknown_path("snap.lxd.daemon.service", raw_path)
                self.assertEqual(result, 2)
                self.assertEqual(stdout, '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"snap.lxd.daemon.service","identity":"UNKNOWN","reason":"SNAP_EXECUTABLE_UNCLASSIFIABLE"}\n')
                self.assertEqual(stderr, "")
                self.assertNotIn("SENTINEL_PATH", stdout + stderr)
                self.assertEqual(len([call for call in runner.calls if call[0] == "/usr/bin/readlink"]), 1)

    def test_diagnose_units_non_snap_unknown_uses_fixed_reason(self) -> None:
        result, stdout, stderr, runner = self._diagnose_unknown_path("lxd.service", b"/private/SENTINEL_EXECUTABLE\n")
        self.assertEqual(result, 2)
        self.assertEqual(stdout, '{"mode":"diagnose-units","status":"BLOCKED_UNKNOWN","unit":"lxd.service","identity":"UNKNOWN","reason":"EXECUTABLE_IDENTITY_BLOCKED"}\n')
        self.assertEqual(stderr, "")
        self.assertNotIn("SENTINEL_EXECUTABLE", stdout + stderr)
        self.assertEqual(len([call for call in runner.calls if call[0] == "/usr/bin/readlink"]), 1)

    def test_diagnose_units_state_drift_stops_before_later_unit(self) -> None:
        rows = {
            "lxd.service": [self._diagnostic_active_service("lxd.service", 51),
                            self._diagnostic_active_service("lxd.service", 52)],
            "snap.lxd.daemon.service": [self._diagnostic_missing_unit("snap.lxd.daemon.service")],
            "snap.lxd.daemon.unix.socket": [self._diagnostic_missing_unit("snap.lxd.daemon.unix.socket", socket=True)],
            "incus.service": [self._diagnostic_missing_unit("incus.service")],
            "incus.socket": [self._diagnostic_missing_unit("incus.socket", socket=True)],
        }
        runner = self._UnitDiagnosticRunner(rows, {51: b"/usr/lib/lxd/lxd\n"})
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), "BLOCKED:UNIT_DRIFT_BLOCKED")
        self.assertEqual([call[2] for call in runner.calls if call[0] == "/usr/bin/systemctl"],
                         ["lxd.service", "lxd.service"])

    def test_diagnose_units_timeout_uses_fixed_error_and_never_writes_artifact(self) -> None:
        rows = {unit: [self._diagnostic_active_service(unit, 61) if unit == "lxd.service"
                       else self._diagnostic_missing_unit(unit, socket=unit.endswith(".socket"))]
                for unit in inventory.UNITS}
        runner = self._UnitDiagnosticRunner(rows, {}, failure=inventory.InventoryError("COMMAND_TIMEOUT"))
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner", return_value=runner), \
                patch.object(inventory, "_write_private") as write, redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units"])
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), "BLOCKED:COMMAND_TIMEOUT")
        self.assertEqual(len(runner.calls), 2)
        write.assert_not_called()

    def test_diagnose_units_extra_arguments_are_rejected_without_echo(self) -> None:
        secret_arg = "/private/SENTINEL_ARGUMENT_PATH"
        stdout, stderr = StringIO(), StringIO()
        with patch.object(inventory, "Runner") as runner, \
                patch.object(inventory, "capture") as capture, redirect_stdout(stdout), redirect_stderr(stderr):
            result = inventory.main(["--diagnose-units", "--output", secret_arg])
        self.assertEqual(result, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().strip(), "BLOCKED:DIAGNOSTIC_ARGUMENTS_INVALID")
        self.assertNotIn(secret_arg, stderr.getvalue())
        self.assertNotIn("usage:", stderr.getvalue().lower())
        runner.assert_not_called()
        capture.assert_not_called()

    def test_artifact_incus_running_socket_requires_matching_service_and_endpoint(self) -> None:
        artifact = self._network_artifact()
        service = next(row for row in artifact["incus_units"] if row["unit"] == "incus.service")
        service.update(load_state="loaded", active_state="active", sub_state="running",
                       unit_file_state="enabled", main_pid=42)
        socket = next(row for row in artifact["incus_units"] if row["unit"] == "incus.socket")
        socket.update(load_state="loaded", active_state="active", sub_state="running",
                      unit_file_state="enabled", main_pid=0, listen="incus_run")
        artifact["incus_executables"] = [{"unit": "incus.service", "main_pid": 42,
                                         "identity_id": "incus_system", "package": "system:incus",
                                         "version": "6.0.5"}]
        endpoint = next(row for row in artifact["sockets"] if row["endpoint_id"] == "incus_run")
        endpoint.update(state="present", unit="incus.socket")
        inventory._validate_artifact(artifact)
        endpoint["state"] = "absent"
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact(artifact)

    def test_executable_identity_is_an_exact_unit_path_pair(self) -> None:
        self.assertEqual(inventory.executable_identity("lxd.service", "/usr/lib/lxd/lxd"),
                         ("lxd_system", "system:lxd"))
        self.assertEqual(inventory.executable_identity("snap.lxd.daemon.service", "/snap/lxd/123/bin/lxd"),
                         ("lxd_snap", "snap:lxd"))
        for unit, path in (("incus.service", "/tmp/incusd"),
                           ("snap.lxd.daemon.service", "/snap/lxd/current/bin/lxd"),
                           ("lxd.service", "/usr/libexec/incus/incusd")):
            with self.subTest(unit=unit, path=path), self.assertRaises(inventory.InventoryError):
                inventory.executable_identity(unit, path)

    def test_source_commit_is_required_to_be_lowercase_full_hash(self) -> None:
        for value in ("", "a" * 39, "A" * 40, "g" * 40):
            with self.subTest(value=value), self.assertRaises(inventory.InventoryError):
                inventory.capture(value, runner=Mock())

    def test_runner_uses_shell_false_devnull_and_sanitized_environment(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 88
        proc.poll.return_value = 0
        proc.wait.return_value = 0
        popen = Mock(return_value=proc)
        runner = inventory.Runner(popen=popen)
        reads = {101: [b"ok", b""], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)):
            status, out, err = runner.run(["/usr/bin/systemctl", "show"], command_id="fixture")
        self.assertEqual((status, out, err), (0, b"ok", b""))
        kwargs = popen.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["env"], {"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
        self.assertTrue(kwargs["start_new_session"])

    def test_runner_rejects_unbounded_or_nonabsolute_argv_and_bad_environment(self) -> None:
        runner = inventory.Runner(popen=Mock())
        for argv, env in ((["systemctl"], None), (["/usr/bin/x", "x\x00y"], None),
                          (["/usr/bin/example"], None),
                          (["/usr/bin/lxc"], {**inventory.ENV_BASE, "HOME": "/tmp"}),
                          (["/usr/bin/lxc"], {**inventory.ENV_BASE, "LXD_SOCKET": "/tmp/x"}),
                          (["/usr/bin/incus"], {**inventory.ENV_BASE, "INCUS_SOCKET": "/var/lib/lxd/unix.socket"})):
            with self.subTest(argv=argv, env=env), self.assertRaises(inventory.InventoryError):
                runner.run(argv, env=env, command_id="test")

    def test_runner_rejects_streams_over_two_mib(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 12
        proc.poll.return_value = None
        proc.kill = Mock()
        proc.wait.side_effect = [None, 0]
        popen = Mock(return_value=proc)
        reads = {101: [b"x" * (inventory.MAX_STREAM + 1)], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)), \
                self.assertRaises(inventory.InventoryError):
            inventory.Runner(popen=popen).run(["/usr/bin/systemctl", "show"], command_id="fixture")

    def test_runner_command_count_and_aggregate_budget_are_hard_limits(self) -> None:
        runner = inventory.Runner(popen=Mock())
        runner.commands = inventory.MAX_COMMANDS
        with self.assertRaises(inventory.InventoryError):
            runner.run(["/usr/bin/systemctl", "show"], command_id="x")
        runner = inventory.Runner(popen=Mock())
        runner.total_bytes = inventory.MAX_TOTAL_BYTES
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 88
        proc.poll.return_value = 0
        proc.wait.return_value = 0
        runner.popen = Mock(return_value=proc)
        reads = {101: [b"x", b""], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)), \
                self.assertRaises(inventory.InventoryError):
            runner.run(["/usr/bin/systemctl", "show"], command_id="x")

    def test_native_command_budget_admits_old_boundary_and_stops_before_overflow_spawn(self) -> None:
        for previous in (256, 2047):
            with self.subTest(previous=previous):
                proc = Mock(pid=88)
                proc.stdout.fileno.return_value = 101
                proc.stderr.fileno.return_value = 102
                proc.poll.return_value = 0
                proc.wait.return_value = 0
                popen = Mock(return_value=proc)
                runner = inventory.Runner(popen=popen, clock=lambda: 0.0)
                runner.commands = previous
                with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                        patch.object(inventory.os, "read", return_value=b""):
                    self.assertEqual(runner.run(["/usr/bin/systemctl", "show"], command_id="fixture"),
                                     (0, b"", b""))
                self.assertEqual(runner.commands, previous + 1)
                self.assertEqual(popen.call_count, 1)
                self.assertEqual(len(runner.records), 1)
                if previous == 2047:
                    before = (runner.commands, runner.total_bytes, list(runner.records))
                    with self.assertRaisesRegex(inventory.InventoryError, "INVENTORY_BUDGET_EXCEEDED"):
                        runner.run(["/usr/bin/systemctl", "show"], command_id="fixture")
                    self.assertEqual(popen.call_count, 1)
                    self.assertEqual((runner.commands, runner.total_bytes, runner.records), before)

    def test_native_larger_command_budget_does_not_extend_wall_or_output_bounds(self) -> None:
        clock = {"now": 0.0}
        popen = Mock()
        runner = inventory.Runner(popen=popen, clock=lambda: clock["now"])
        clock["now"] = 301.0
        with self.assertRaisesRegex(inventory.InventoryError, "INVENTORY_BUDGET_EXCEEDED"):
            runner.run(["/usr/bin/systemctl", "show"], command_id="fixture")
        popen.assert_not_called()
        self.assertEqual(runner.commands, 0)
        proc = Mock(pid=88)
        proc.stdout.fileno.return_value = 101
        proc.stderr.fileno.return_value = 102
        proc.poll.return_value = 0
        proc.wait.return_value = 0
        runner = inventory.Runner(popen=Mock(return_value=proc), clock=lambda: 0.0)
        runner.total_bytes = 16 * 1024 * 1024
        reads = {101: [b"x", b""], 102: [b""]}
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "read", side_effect=lambda fd, _n: reads[fd].pop(0)), \
                patch.object(inventory, "_kill_reap") as cleanup:
            with self.assertRaisesRegex(inventory.InventoryError, "TOTAL_OUTPUT_LIMIT"):
                runner.run(["/usr/bin/systemctl", "show"], command_id="fixture")
        self.assertEqual(runner.commands, 1)
        self.assertEqual(runner.records, [])
        cleanup.assert_called_once_with(proc)

    def test_native_artifact_command_record_count_has_the_same_finite_boundary(self) -> None:
        record = {"command_id": "systemctl_show_unit", "safe_args": ["incus.service"],
                  "exit_status": 0, "stdout_bytes": 0, "stderr_bytes": 0}
        artifact = self._valid_artifact([record] * 2048)
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))
        artifact["command_records"].append(record)
        with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_COMMANDS_INVALID"):
            inventory._validate_artifact(artifact)

    def test_endpoint_allowlist_rejects_unrecognized_paths_and_non_socket(self) -> None:
        self.assertEqual(inventory.SOCKETS["/var/lib/incus/unix.socket"], "incus_var_lib")
        self.assertNotIn("/tmp/unknown.sock", inventory.SOCKETS)
        with self.assertRaises(inventory.InventoryError):
            inventory._endpoint(Mock(), "/tmp/unknown.sock", unit="")

    @staticmethod
    def _api_response(metadata):
        return {"type": "sync", "status": "Success", "status_code": 200,
                "operation": "", "error_code": 0, "error": "", "metadata": metadata}

    def test_detail_path_templates_encode_validated_components_and_explicit_project(self) -> None:
        cases = [
            ("projects", ("a+b",), "a+b", "/1.0/projects/a%2Bb?project=a%2Bb"),
            ("profiles", ("a+b",), "p+q", "/1.0/profiles/a%2Bb?project=p%2Bq"),
            ("instances", ("web",), "default", "/1.0/instances/web?project=default"),
            ("instance-list", (), "p+q", "/1.0/instances?project=p%2Bq&recursion=1"),
            ("networks", ("net",), "default", "/1.0/networks/net?project=default"),
            ("storage-pools", ("pool",), "default", "/1.0/storage-pools/pool?project=default"),
            ("storage-volumes", ("pool", "virtual-machine", "web"), "default",
             "/1.0/storage-pools/pool/volumes/virtual-machine/web?project=default"),
        ]
        for kind, names, project, expected in cases:
            with self.subTest(kind=kind):
                self.assertEqual(inventory._detail_uri(kind, names, project), expected)

    def test_detail_rejects_injected_or_unknown_paths_before_execution(self) -> None:
        runner = Mock()
        env = {**inventory.ENV_BASE, "INCUS_SOCKET": "/run/incus/unix.socket"}
        cases = [("unknown", ("web",), "alpha"), ("profiles", (), "alpha"),
                 ("profiles", ("web", "other"), "alpha"),
                 ("instance-list", ("recursion=2",), "alpha"),
                 ("projects", ("other",), "alpha"),
                 ("storage-volumes", ("pool", "DELETE", "web"), "alpha")]
        for value in ("../web", ".", "..", "/web", "web?project=other", "web#x", "web%2Fx",
                      "remote:web", "https://remote/web", "--request=DELETE", "--data", "web\n"):
            cases.extend([("profiles", (value,), "alpha"), ("profiles", ("web",), value)])
        for kind, names, project in cases:
            with self.subTest(kind=kind, names=names, project=project):
                with self.assertRaises(inventory.InventoryError):
                    inventory._detail(runner, ["/usr/bin/incus", "--force-local"], kind, names, project,
                                      command_id="incus_profile_show", env=env, safe_args=[])
        for prefix in (["incus", "--force-local"], ["/usr/bin/incus", "--project", "alpha"],
                       ["/usr/bin/incus", "--force-local", "--request", "DELETE"]):
            with self.assertRaises(inventory.InventoryError):
                inventory._detail(runner, prefix, "profiles", ("web",), "alpha",
                                  command_id="incus_profile_show", env=env, safe_args=[])
        runner.run.assert_not_called()

    def test_raw_detail_rejects_zero_exit_error_async_or_malformed_envelopes(self) -> None:
        valid = self._api_response({"name": "web"})
        invalid: list[Any] = [None, [], {**valid, "unknown": "value"}]
        invalid.extend({k: v for k, v in valid.items() if k != omitted} for omitted in valid)
        mutations: dict[str, list[Any]] = {
            "type": ["async", "error", None], "status": ["Failure", "success"],
            "status_code": [True, "200", 200.0, 400], "operation": ["/1.0/operations/private", None],
            "error_code": [False, "0", 0.0, 403], "error": ["private-message", None],
            "metadata": [None, [], "value"],
        }
        for key, values in mutations.items():
            invalid.extend({**valid, key: value} for value in values)
        for response in invalid:
            with self.subTest(response=response):
                runner = Mock()
                runner.run.return_value = (0, json.dumps(response).encode(), b"")
                with self.assertRaisesRegex(inventory.InventoryError, "API_RESPONSE_INVALID"):
                    inventory._detail(runner, ["/snap/bin/lxc", "--force-local"], "profiles", ("web",), "alpha",
                                      command_id="lxd_profile_show", env={}, safe_args=[])

    def test_raw_detail_preserves_strict_nested_duplicate_json_rejection(self) -> None:
        valid = json.dumps(self._api_response({"name": "web"})).encode()
        for raw in (b"{", valid.replace(b'"name": "web"', b'"name":"web","name":"other"'),
                    valid.replace(b'"type": "sync"', b'"type":"sync","type":"sync"'),
                    valid.replace(b'"name": "web"', b'"name":NaN')):
            with self.subTest(raw=raw):
                runner = Mock()
                runner.run.return_value = (0, raw, b"")
                with self.assertRaises(inventory.InventoryError):
                    inventory._detail(runner, ["/usr/bin/incus", "--force-local"], "profiles", ("web",), "alpha",
                                      command_id="incus_profile_show", env={}, safe_args=[])

    def test_instance_collection_requires_bounded_array_metadata(self) -> None:
        runner = Mock()
        env = {**inventory.ENV_BASE, "INCUS_SOCKET": "/run/incus/unix.socket"}
        metadata: Any
        for metadata in (None, {}, "value", 2):
            with self.subTest(metadata=metadata):
                runner.run.return_value = (0, json.dumps(self._api_response(metadata)).encode(), b"")
                with self.assertRaisesRegex(inventory.InventoryError, "API_RESPONSE_INVALID"):
                    inventory._detail(runner, ["/usr/bin/incus", "--force-local"], "instance-list", (), "alpha",
                                      command_id="incus_instance_list", env=env, safe_args=["alpha"])
        runner.run.return_value = (0, json.dumps(self._api_response([{}] * 8)).encode(), b"")
        with patch.object(inventory, "MAX_ENTITIES", 7):
            with self.assertRaisesRegex(inventory.InventoryError, "ENTITY_LIMIT"):
                inventory._detail(runner, ["/usr/bin/incus", "--force-local"], "instance-list", (), "alpha",
                                  command_id="incus_instance_list", env=env, safe_args=["alpha"])
        runner.run.return_value = (0, json.dumps(self._api_response([])).encode(), b"")
        self.assertEqual(inventory._detail(runner, ["/usr/bin/incus", "--force-local"], "instance-list", (), "alpha",
                                          command_id="incus_instance_list", env=env, safe_args=["alpha"]), [])
        runner.run.assert_called_with(
            ["/usr/bin/incus", "--force-local", "query", "--request", "GET", "--raw",
             "/1.0/instances?project=alpha&recursion=1"], env=env, command_id="incus_instance_list", safe_args=["alpha"])

    def test_instance_collection_rejects_full_state_fields_and_nonobject_rows(self) -> None:
        base = {"name": "web", "project": "alpha", "config": {}, "devices": {}, "ephemeral": False,
                "profiles": ["bravo"], "stateful": False, "type": "container", "status": "Running"}
        for extra in ("state", "backups", "snapshots"):
            runner = self._InventoryRunner()
            runner.list_rows["instances"] = [{**base, extra: []}]
            with self.subTest(extra=extra), self.assertRaisesRegex(inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
                inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket", incus=True,
                                            before_query=lambda: None)
        runner = self._InventoryRunner()
        runner.list_rows["instances"] = [None]  # type: ignore[list-item]
        with self.assertRaisesRegex(inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
            inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket", incus=True,
                                        before_query=lambda: None)
        with self.assertRaises(AssertionError):
            self._InventoryRunner().run(["/snap/bin/lxc", "--force-local", "list", "--project", "alpha", "--format", "json"],
                                        command_id="lxd_instance_list")

    def test_historical_unsupported_show_json_is_not_a_fixture_contract(self) -> None:
        with self.assertRaises(AssertionError):
            self._InventoryRunner().run(
                ["/snap/bin/lxc", "--force-local", "project", "show", "alpha", "--format", "json"],
                command_id="lxd_project_show")

    def test_every_inventory_request_is_prechecked_and_independent_devices_survive(self) -> None:
        runner = self._InventoryRunner()
        checks = Mock()
        _, rows = inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                               incus=True, before_query=checks)
        self.assertEqual(checks.call_count, len(runner.calls))
        instance = rows[0]["instances"][0]
        self.assertEqual(instance["local_devices"], [])
        self.assertEqual(instance["expanded_devices"], [{"name": "eth0", "type": "nic"},
                                                        {"name": "root", "type": "disk"}])
        self.assertNotIn("security.nesting", str(rows))

    def test_instance_api_omitted_empty_maps_are_not_local_fallbacks(self) -> None:
        instance = {"name": "web", "config": {"private": "value"},
                    "devices": {"local": {"type": "disk", "source": "/private"}},
                    "ephemeral": False, "profiles": [], "stateful": False}
        parsed = inventory._validate_instance_config(instance, "web", "alpha")
        self.assertEqual(parsed["expanded_config"], {})
        self.assertEqual(parsed["expanded_devices"], {})
        for key, value in (("expanded_config", None), ("expanded_devices", []),
                           ("status_code", True), ("created_at", 5), ("unknown", "value")):
            with self.subTest(key=key):
                with self.assertRaises(inventory.InventoryError):
                    inventory._validate_instance_config({**instance, key: value}, "web", "alpha")

    def test_instance_api_rejects_drift_or_unknown_fields_before_projection(self) -> None:
        changes: list[dict[str, Any]] = [{"config": {"changed": "yes"}}, {"devices": {}},
                   {"expanded_devices": {}}, {"expanded_config": {}},
                   {"profiles": []}, {"project": "other"}, {"name": "other"},
                   {"location": "other"}, {"created_at": "other"}, {"private_new_field": "value"}]
        # The local device map starts empty; use a nonempty map for its drift case.
        changes[1] = {"devices": {"new": {"type": "disk"}}}
        for change in changes:
            with self.subTest(change=change):
                runner = self._InventoryRunner()
                runner.detail_overrides["incus_instance_config_show_expanded"] = change
                with self.assertRaises(inventory.InventoryError):
                    inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                incus=True, before_query=lambda: None)
                self.assertEqual(runner.calls[-1][2], "incus_instance_config_show_expanded")
        runner = self._InventoryRunner()
        runner.detail_overrides["incus_instance_config_show_expanded"] = {
            "status": "Stopped", "status_code": 102, "last_used_at": "2026-11-07T00:00:00Z"}
        inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                    incus=True, before_query=lambda: None)

    def test_detail_responses_are_validated_then_reduced_to_safe_identity(self) -> None:
        profile = {"name": "default", "project": "alpha", "description": "", "config": {},
                   "devices": {"eth0": {"type": "nic", "parent": "br0"}},
                   "used_by": ["/1.0/instances/web"]}
        parsed = inventory._validate_profile_show(profile, "default", "alpha")
        self.assertEqual(inventory._consumer_refs(parsed["used_by"], "default"),
                         [{"kind": "instances", "name": "web", "project": "default"}])
        self.assertEqual(inventory._device_types(parsed["devices"]), [{"name": "eth0", "type": "nic"}])
        private_device = inventory._validate_profile_show(
            {**profile, "devices": {"secret": {"type": "disk", "source": "/host/private"}}}, "default", "alpha")
        projected = inventory._device_types(private_device["devices"])
        self.assertEqual(projected, [{"name": "secret", "type": "disk"}])
        self.assertNotIn("source", str(projected))
        self.assertNotIn("/host/private", str(projected))
        with self.assertRaises(inventory.InventoryError):
            inventory._consumer_refs(["https://host/1.0/instances/web"], "alpha")
        self.assertEqual(inventory._consumer_refs(
            ["/1.0/storage-pools/default/volumes/container/web?project=alpha"], "alpha"),
            [{"kind": "storage-volumes", "name": "default/container/web", "project": "alpha"}])
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_profile_show({**profile, "project": "other"}, "default", "alpha")

    def test_instance_detail_requires_both_config_shapes(self) -> None:
        instance = {"name": "web", "config": {}, "devices": {}, "ephemeral": False,
                    "profiles": ["default"], "stateful": False}
        self.assertEqual(inventory._validate_instance_config(instance, "web", "alpha")["name"], "web")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_instance_config({**instance, "unknown": "value"}, "web", "alpha")

    def test_nullable_cluster_locations_are_validated_without_mutating_metadata(self) -> None:
        network: dict[str, Any] = {"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                   "config": {}, "used_by": []}
        pool: dict[str, Any] = {"name": "pool", "project": "alpha", "driver": "dir", "config": {}, "used_by": []}
        locations: Any
        for locations in (None, [], ["member-1"]):
            for base, validator in ((network, inventory._validate_network_show),
                                    (pool, inventory._validate_pool_show)):
                row = {**base, "locations": locations}
                before = json.dumps(row)
                self.assertEqual(validator(row, base["name"], "alpha"), row)
                self.assertEqual(json.dumps(row), before)
        for locations in (False, 0, "", {}, [None], [2], [["member-1"]]):
            for base, validator in ((network, inventory._validate_network_show),
                                    (pool, inventory._validate_pool_show)):
                with self.subTest(locations=locations, name=base["name"]):
                    with self.assertRaises(inventory.InventoryError):
                        validator({**base, "locations": locations}, base["name"], "alpha")

    def test_nullable_locations_keep_projection_and_ownership_checks_unchanged(self) -> None:
        runner = self._InventoryRunner()
        _, expected = inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                   incus=True, before_query=lambda: None)
        runner = self._InventoryRunner()
        runner.list_rows["networks"] = [{"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                                         "config": {}, "used_by": runner.network_used_by, "locations": None}]
        runner.list_rows["pools"] = [{"name": "pool", "project": "alpha", "driver": "dir", "config": {},
                                      "used_by": runner.pool_used_by, "locations": None, "description": "", "status": "Created"}]
        runner.detail_overrides["incus_network_show"] = {"locations": None}
        runner.detail_overrides["incus_storage_show"] = {"locations": None}
        _, actual = inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                 incus=True, before_query=lambda: None)
        for project_rows in (actual, expected):
            for project_row in project_rows:
                for pool in project_row["pools"]:
                    pool.pop("metadata_digest")
        self.assertEqual(actual, expected)
        self.assertIsNone(runner.list_rows["networks"][0]["locations"])
        self.assertIsNone(runner.list_rows["pools"][0]["locations"])
        self.assertNotIn("locations", str(actual))
        for field in ("config", "used_by", "name", "project"):
            with self.subTest(field=field):
                runner = self._InventoryRunner()
                runner.detail_overrides["incus_network_show"] = {"locations": None, field: None}
                with self.assertRaises(inventory.InventoryError):
                    inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                incus=True, before_query=lambda: None)

    def test_network_and_pool_detail_reject_project_scope_mismatch(self) -> None:
        network = {"name": "br0", "project": "alpha", "type": "bridge", "managed": True, "config": {}, "used_by": []}
        pool = {"name": "default", "project": "alpha", "driver": "dir", "config": {}, "used_by": []}
        self.assertEqual(inventory._validate_network_show(network, "br0", "alpha")["name"], "br0")
        self.assertEqual(inventory._validate_pool_show(pool, "default", "alpha")["name"], "default")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_network_show({**network, "project": "beta"}, "br0", "alpha")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_pool_show({**pool, "project": "beta"}, "default", "alpha")

    def test_network_and_pool_details_require_consumer_relationships(self) -> None:
        network = {"name": "br0", "project": "alpha", "type": "bridge", "managed": True, "config": {}}
        pool = {"name": "default", "project": "alpha", "driver": "dir", "config": {}}
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_network_show(network, "br0", "alpha")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_pool_show(pool, "default", "alpha")

    def test_unknown_storage_volume_type_fails_closed(self) -> None:
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_TYPE_UNSUPPORTED"):
            inventory._volume_type("future-volume-kind")

    def test_runner_requires_client_specific_canonical_socket(self) -> None:
        runner = inventory.Runner(popen=Mock())
        for binary, env in (("/usr/bin/lxc", {**inventory.ENV_BASE, "INCUS_SOCKET": "/run/incus/unix.socket"}),
                            ("/usr/bin/incus", {**inventory.ENV_BASE, "INCUS_SOCKET": "/tmp/socket"}),
                            ("/usr/bin/lxc", {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/incus/unix.socket"}),
                            ("/snap/bin/lxc", {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"})):
            with self.subTest(binary=binary, env=env), self.assertRaises(inventory.InventoryError):
                runner.run([binary, "--force-local", "version"], env=env, command_id="version")

    def test_inventory_preserves_plain_and_exact_lts_server_version(self) -> None:
        for version, newline in (("6.0.5", "\n"), ("5.21.9 LTS", "\n"), ("5.21.9 LTS", "\r\n")):
            with self.subTest(version=version, newline=newline):
                runner = self._InventoryRunner()
                runner.version_output = ("Client version: " + version + newline + "Server version: " + version + newline).encode()
                observed, projects = inventory._inventory_client(
                    runner, "lxd_snap", "/var/snap/lxd/common/lxd/unix.socket", incus=False, before_query=lambda: None)
                self.assertEqual(observed, version)
                self.assertEqual(len(projects), 2)
                self.assertIn(["project", "list", "--format", "json"], [call[0][2:] for call in runner.calls])

    def test_invalid_or_duplicate_version_records_block_before_resource_queries(self) -> None:
        values = [b"5.21.9  LTS", b"5.21.9\tLTS", b"5.21.9 lts", b"5.21.9 LTS extra", b"5.21.9 preview", b"",
                  b"5.21.9\nServer version: 5.21.9 LTS", b"5.21.9\nServer version: malformed value", b"\xff"]
        for value in values:
            with self.subTest(value=value):
                runner = self._InventoryRunner()
                runner.version_output = b"Client version: 5.21.9 LTS\nServer version: " + value + b"\n"
                before = Mock()
                code = "VERSION_OUTPUT_INVALID" if value == b"\xff" else "VERSION_SCHEMA_INVALID"
                with self.assertRaisesRegex(inventory.InventoryError, "^" + code + "$"):
                    inventory._inventory_client(runner, "lxd_snap", "/var/snap/lxd/common/lxd/unix.socket",
                                                incus=False, before_query=before)
                self.assertEqual([call[0][2:] for call in runner.calls], [["version"]])
                before.assert_called_once_with()

    def test_inventory_client_uses_exact_detail_argv_and_projects_safe_consumer_identity(self) -> None:
        runner = self._InventoryRunner()
        version, projects = inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket",
                                                          incus=False, before_query=lambda: None)
        self.assertEqual(version, "6.0.5")
        suffixes = [call[0][2:] for call in runner.calls]
        self.assertEqual(suffixes, [
            ["version"], ["query", "--request", "GET", "--raw", "/1.0"], ["project", "list", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/projects/alpha?project=alpha"],
            ["profile", "list", "--project", "alpha", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/instances?project=alpha&recursion=1"],
            ["network", "list", "--project", "alpha", "--format", "json"],
            ["storage", "list", "--project", "alpha", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/profiles/zeta?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/profiles/bravo?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/instances/web?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/instances/web?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/networks/net?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool?project=alpha"],
            ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool/volumes/container/web?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/projects/default?project=default"],
            ["profile", "list", "--project", "default", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/instances?project=default&recursion=1"],
            ["network", "list", "--project", "default", "--format", "json"],
            ["storage", "list", "--project", "default", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool?project=default"],
            ["storage", "volume", "list", "pool", "--project", "default", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0"],
        ])
        self.assertTrue(all(call[1] == {**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"}
                            for call in runner.calls))
        self.assertEqual([row["name"] for row in projects[0]["profiles"]], ["bravo", "zeta"])
        self.assertEqual(projects[0]["profiles"][0]["used_by"], [
            {"kind": "instances", "name": "web", "project": "alpha"},
        ])

    def test_incus_inventory_uses_exact_detail_argv_binary_and_socket_environment(self) -> None:
        runner = self._InventoryRunner()
        version, projects = inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                          incus=True, before_query=lambda: None)
        self.assertEqual(version, "6.0.5")
        self.assertEqual(len(projects), 2)
        self.assertTrue(all(call[0][0:2] == ["/usr/bin/incus", "--force-local"] for call in runner.calls))
        self.assertTrue(all(call[1] == {**inventory.ENV_BASE, "INCUS_SOCKET": "/run/incus/unix.socket"}
                            for call in runner.calls))
        self.assertEqual([call[0][2:] for call in runner.calls], [
            ["version"], ["query", "--request", "GET", "--raw", "/1.0"], ["project", "list", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/projects/alpha?project=alpha"],
            ["profile", "list", "--project", "alpha", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/instances?project=alpha&recursion=1"],
            ["network", "list", "--project", "alpha", "--format", "json"],
            ["storage", "list", "--project", "alpha", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/profiles/zeta?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/profiles/bravo?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/instances/web?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/instances/web?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/networks/net?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool?project=alpha"],
            ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool/volumes/container/web?project=alpha"],
            ["query", "--request", "GET", "--raw", "/1.0/projects/default?project=default"],
            ["profile", "list", "--project", "default", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/instances?project=default&recursion=1"],
            ["network", "list", "--project", "default", "--format", "json"],
            ["storage", "list", "--project", "default", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool?project=default"],
            ["storage", "volume", "list", "pool", "--project", "default", "--format", "json"],
            ["query", "--request", "GET", "--raw", "/1.0"],
        ])
        self.assertIn("incus_profile_show", [record["command_id"] for record in runner.records])
        self.assertIn("incus_network_show", [record["command_id"] for record in runner.records])
        self.assertIn("incus_storage_show", [record["command_id"] for record in runner.records])
        self.assertTrue(all(record["command_id"].startswith("incus_") for record in runner.records))

    def test_capture_rechecks_each_query_and_returns_complete_sorted_projection(self) -> None:
        runner = self._InventoryRunner()
        def active(unit, pid):
            return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": pid}
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        incus_socket = {"unit": "incus.socket", "load_state": "loaded", "active_state": "active",
                        "sub_state": "running", "unit_file_state": "enabled", "main_pid": 0,
                        "listen": "incus_run"}
        unit_rows = {"lxd.service": active("lxd.service", 42),
                     "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                     "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                     "incus.service": active("incus.service", 43), "incus.socket": incus_socket}
        endpoint_present = {"/var/lib/lxd/unix.socket", "/run/incus/unix.socket"}
        checked: list[bool] = []
        real_recheck = inventory._recheck_all
        def record_recheck(*args: Any) -> None:
            checked.append(True)
            real_recheck(*args)
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: dict(unit_rows[unit])), \
                patch.object(inventory, "_resolve_executable", side_effect=lambda _runner, row:
                             ("incus_system", "system:incus") if row["unit"] == "incus.service"
                             else ("lxd_system", "system:lxd")), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit:
                             (inventory.SOCKETS[path], path in endpoint_present)), \
                patch.object(inventory, "_recheck_all", side_effect=record_recheck), \
                patch.object(inventory, "_require_full_local_access"):
            artifact = inventory.capture("a" * 40, runner=runner)
        self.assertEqual(len(checked), len(runner.calls) + 1)
        self.assertEqual(artifact["decision"], "READ_ONLY_INVENTORY_COMPLETE")
        self.assertEqual(artifact["incus_units"][1]["sub_state"], "running")
        self.assertEqual(artifact["incus_executables"][0]["identity_id"], "incus_system")
        self.assertEqual([row["name"] for row in artifact["lxd_projects"][0]["profiles"]], ["bravo", "zeta"])
        self.assertEqual([row["name"] for row in artifact["lxd_projects"][0]["networks"]], ["net"])
        self.assertTrue(artifact["incus_projects"])
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))

    def test_running_incus_socket_drift_blocks_before_first_client_query(self) -> None:
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        units = {unit: missing(unit, unit.endswith(".socket")) for unit in inventory.UNITS}
        units["incus.service"] = {"unit": "incus.service", "load_state": "loaded", "active_state": "active",
                                  "sub_state": "running", "unit_file_state": "enabled", "main_pid": 43}
        units["incus.socket"] = {"unit": "incus.socket", "load_state": "loaded", "active_state": "active",
                                 "sub_state": "running", "unit_file_state": "enabled", "main_pid": 0,
                                 "listen": "incus_run"}
        counts = {unit: 0 for unit in inventory.UNITS}
        runner = self._InventoryRunner()
        def systemctl(_runner, unit):
            counts[unit] += 1
            row = dict(units[unit])
            if unit == "incus.socket" and counts[unit] == 2:
                row["sub_state"] = "listening"
            return row
        with patch.object(inventory, "_systemctl_show", side_effect=systemctl), \
                patch.object(inventory, "_resolve_executable", return_value=("incus_system", "system:incus")), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit:
                             (inventory.SOCKETS[path], path == "/run/incus/unix.socket")), \
                patch.object(inventory, "_require_full_local_access"):
            with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_UNIT_DRIFT"):
                inventory.capture("a" * 40, runner=runner)
        self.assertEqual(runner.calls, [])

    def test_service_or_socket_drift_blocks_the_next_cli_query(self) -> None:
        def active(unit, pid):
            return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": pid}
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        base = {"lxd.service": active("lxd.service", 42),
                "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                "incus.service": missing("incus.service"), "incus.socket": missing("incus.socket", True)}
        for drift in ("service", "socket"):
            with self.subTest(drift=drift):
                calls = {"unit": 0, "endpoint": 0}
                runner = self._InventoryRunner()
                def systemctl(_runner, unit):
                    if unit == "lxd.service":
                        calls["unit"] += 1
                        if drift == "service" and calls["unit"] == 2:
                            return {**base[unit], "main_pid": 43}
                    return dict(base[unit])
                def endpoint(_runner, path, unit):
                    present = path == "/var/lib/lxd/unix.socket"
                    if path == "/var/lib/lxd/unix.socket":
                        calls["endpoint"] += 1
                        if drift == "socket" and calls["endpoint"] == 2:
                            present = False
                    return inventory.SOCKETS[path], present
                with patch.object(inventory, "_systemctl_show", side_effect=systemctl), \
                        patch.object(inventory, "_resolve_executable", return_value=("lxd_system", "system:lxd")), \
                        patch.object(inventory, "_endpoint", side_effect=endpoint):
                    with self.assertRaises(inventory.InventoryError):
                        inventory.capture("a" * 40, runner=runner)
                self.assertEqual(runner.calls, [])

    def test_competing_service_appearing_during_capture_creates_no_query_or_artifact(self) -> None:
        def active(unit, pid):
            return {"unit": unit, "load_state": "loaded", "active_state": "active", "sub_state": "running",
                    "unit_file_state": "enabled", "main_pid": pid}
        def missing(unit, socket=False):
            row = {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                   "unit_file_state": "", "main_pid": 0}
            if socket:
                row["listen"] = ""
            return row
        units = {"lxd.service": active("lxd.service", 42),
                 "snap.lxd.daemon.service": missing("snap.lxd.daemon.service"),
                 "snap.lxd.daemon.unix.socket": missing("snap.lxd.daemon.unix.socket", True),
                 "incus.service": missing("incus.service"), "incus.socket": missing("incus.socket", True)}
        counts = {unit: 0 for unit in inventory.UNITS}
        runner = self._InventoryRunner()
        def systemctl(_runner, unit):
            counts[unit] += 1
            if unit == "snap.lxd.daemon.service" and counts[unit] == 2:
                return active(unit, 73)
            return dict(units[unit])
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "blocked-inventory.json"
            with patch.object(inventory, "Runner", return_value=runner), \
                    patch.object(inventory, "_systemctl_show", side_effect=systemctl), \
                    patch.object(inventory, "_resolve_executable", return_value=("lxd_system", "system:lxd")), \
                    patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], path == "/var/lib/lxd/unix.socket")), \
                    patch.object(inventory, "_require_full_local_access"), \
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(artifact)])
            self.assertEqual(result, 2)
            self.assertFalse(artifact.exists())
            self.assertEqual(runner.calls, [])
            self.assertGreaterEqual(counts["lxd.service"], 1)
            self.assertEqual(counts["snap.lxd.daemon.service"], 2)
            write.assert_not_called()
            self.assertIn("BLOCKED:RUNTIME_UNIT_DRIFT", stderr.getvalue())

    def test_loaded_inactive_incus_and_no_active_runtime_fail_closed(self) -> None:
        with patch.object(inventory, "_systemctl_show") as show, patch.object(inventory, "_resolve_executable") as resolve, \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], False)):
            rows = {unit: {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                           "unit_file_state": "", "main_pid": 0} for unit in inventory.UNITS}
            for unit in ("snap.lxd.daemon.unix.socket", "incus.socket"):
                rows[unit]["listen"] = ""
            rows["incus.service"] = {"unit": "incus.service", "load_state": "loaded", "active_state": "inactive",
                                     "sub_state": "dead", "unit_file_state": "enabled", "main_pid": 0}
            show.side_effect = lambda _runner, unit: rows[unit]
            resolve.side_effect = AssertionError("inactive process must not be resolved")
            with self.assertRaises(inventory.InventoryError):
                inventory.capture("a" * 40, runner=Mock())

    def test_no_installed_or_active_runtime_fails_instead_of_empty_success(self) -> None:
        rows = {unit: {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                       "unit_file_state": "", "main_pid": 0} for unit in inventory.UNITS}
        for unit in ("snap.lxd.daemon.unix.socket", "incus.socket"):
            rows[unit]["listen"] = ""
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit: (inventory.SOCKETS[path], False)):
            with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_INVENTORY_EMPTY"):
                inventory.capture("a" * 40, runner=Mock())

    def test_incus_active_does_not_mask_residual_unavailable_lxd_endpoint(self) -> None:
        for residual in ("socket_unit", "endpoint"):
            with self.subTest(residual=residual):
                rows = {unit: {"unit": unit, "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                               "unit_file_state": "", "main_pid": 0} for unit in inventory.UNITS}
                for unit in ("snap.lxd.daemon.unix.socket", "incus.socket"):
                    rows[unit]["listen"] = ""
                if residual == "socket_unit":
                    rows["snap.lxd.daemon.unix.socket"] = {"unit": "snap.lxd.daemon.unix.socket", "load_state": "loaded",
                        "active_state": "active", "sub_state": "listening", "unit_file_state": "enabled",
                        "main_pid": 0, "listen": "lxd_system"}
                rows["incus.service"] = {"unit": "incus.service", "load_state": "loaded", "active_state": "active",
                                         "sub_state": "running", "unit_file_state": "enabled", "main_pid": 77}
                def endpoint(_runner, path, unit):
                    return inventory.SOCKETS[path], residual == "endpoint" and path == "/var/lib/lxd/unix.socket"
                with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                        patch.object(inventory, "_resolve_executable", return_value=("incus_system", "system:incus")), \
                        patch.object(inventory, "_endpoint", side_effect=endpoint):
                    with self.assertRaisesRegex(inventory.InventoryError, "LXD_RUNTIME_INVENTORY_UNAVAILABLE"):
                        inventory.capture("a" * 40, runner=Mock())

    def test_unknown_resource_fields_fail_closed(self) -> None:
        self.assertEqual(inventory._only_keys({"name": "default"}, {"name"}), {"name": "default"})
        with self.assertRaises(inventory.InventoryError):
            inventory._only_keys({"name": "default", "config": {"secret": "redacted"}}, {"name"})

    def test_complete_ownership_requires_resolvable_profile_and_consumer_edges(self) -> None:
        _version, projects = inventory._inventory_client(
            self._InventoryRunner(), "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None)
        inventory._validate_complete_ownership(projects)

        projects[0]["instances"][0]["profiles"] = ["missing"]
        with self.assertRaisesRegex(inventory.InventoryError, "PROFILE_REFERENCE_UNRESOLVED"):
            inventory._validate_complete_ownership(projects)

        _version, projects = inventory._inventory_client(
            self._InventoryRunner(), "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None)
        projects[0]["networks"][0]["used_by"] = [
            {"kind": "instances", "name": "missing", "project": "alpha"}]
        with self.assertRaisesRegex(inventory.InventoryError, "CONSUMER_REFERENCE_UNRESOLVED"):
            inventory._validate_complete_ownership(projects)

        _version, projects = inventory._inventory_client(
            self._InventoryRunner(), "incus_system", "/run/incus/unix.socket", incus=True,
            before_query=lambda: None)
        projects[0]["profiles"][0]["used_by"] = []
        with self.assertRaisesRegex(inventory.InventoryError, "PROFILE_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._validate_complete_ownership(projects)

    def test_project_used_by_accepts_complete_inventory_and_rejects_missing_or_unknown_users(self) -> None:
        runner = self._InventoryRunner()
        _version, projects = inventory._inventory_client(
            runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)
        self.assertEqual(projects[0]["project"], "alpha")

        runner = self._InventoryRunner()
        runner.project_used_by = ["/1.0/instances/missing?project=alpha"]
        with self.assertRaisesRegex(inventory.InventoryError, "PROJECT_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.project_used_by.append("/1.0/images/fingerprint?project=alpha")
        with self.assertRaises(inventory.InventoryError):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_volume_detail_created_at_must_be_a_string_when_present(self) -> None:
        volume = {"name": "data", "type": "custom", "content_type": "filesystem", "project": "alpha",
                  "config": {}, "used_by": [], "created_at": "2026-10-01T00:00:00Z"}
        self.assertEqual(inventory._validate_volume_show(volume, "pool", "custom", "data", "alpha", incus=True)["name"], "data")
        with self.assertRaisesRegex(inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
            inventory._validate_volume_show({**volume, "created_at": 123}, "pool", "custom", "data", "alpha", incus=True)
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_OWNER_PROJECT_UNSUPPORTED"):
            inventory._validate_volume_show({**volume, "project": "default"}, "pool", "custom", "data", "alpha", incus=True)

    def test_volume_family_pool_identity_preserves_normalized_schema_two_graph(self) -> None:
        incus_runner = self._InventoryRunner()
        incus_rows = inventory._inventory_client(incus_runner, "incus_system", "/run/incus/unix.socket",
                                                incus=True, before_query=lambda: None)[1]
        for identity in ("lxd_system", "lxd_snap"):
            runner = self._InventoryRunner()
            runner.version_output = b"Client version: 5.21.9\nServer version: 5.21.9 LTS\n"
            version, rows = inventory._inventory_client(runner, identity,
                "/var/lib/lxd/unix.socket" if identity == "lxd_system" else "/var/snap/lxd/common/lxd/unix.socket",
                incus=False, before_query=lambda: None)
            self.assertEqual(version, "5.21.9 LTS")
            self.assertEqual(rows, incus_rows)
            volume = rows[0]["pools"][0]["volumes"][0]
            self.assertEqual(set(volume), {"name", "type", "content_type", "owner_project", "storage_location", "used_by"})
            volume_calls = [call[0][2:] for call in runner.calls if call[2] in {
                "lxd_storage_volume_list", "lxd_storage_volume_show"}]
            self.assertEqual(volume_calls, [
                ["storage", "volume", "list", "pool", "--project", "alpha", "--format", "json"],
                ["query", "--request", "GET", "--raw", "/1.0/storage-pools/pool/volumes/container/web?project=alpha"],
                ["storage", "volume", "list", "pool", "--project", "default", "--format", "json"],
            ])
            artifact = self._valid_artifact()
            self._bind_artifact(artifact, rows, incus=False, cli_version="5.21.9 LTS")
            self.assertEqual(json.loads(inventory._validate_artifact(artifact))["schema_version"], 4)

    def test_lxd_malformed_pool_blocks_each_real_adapter_boundary(self) -> None:
        malformed_pools: tuple[object, ...] = (None, False, True, 0, 1.0, [], {}, "", " pool", "pool\n",
                                              "../pool", "/pool", "po%6fl", "POOL", "other", "pöol")
        for boundary in ("list", "detail"):
            for malformed_pool in malformed_pools:
                runner = self._InventoryRunner()
                if boundary == "list":
                    runner.volume_list_pool = malformed_pool
                else:
                    runner.volume_detail_pool = malformed_pool
                with self.subTest(boundary=boundary, pool=malformed_pool):
                    with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_POOL_IDENTITY_MISMATCH"):
                        inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket",
                                                    incus=False, before_query=lambda: None)
                    detail_count = sum(call[2] == "lxd_storage_volume_show" for call in runner.calls)
                    self.assertEqual(detail_count, 0 if boundary == "list" else 1)

    def test_lxd_missing_pool_blocks_main_before_private_artifact_write(self) -> None:
        for boundary in ("list", "detail"):
            runner = self._InventoryRunner()
            runner.omit_volume_list_pool = boundary == "list"
            runner.omit_volume_detail_pool = boundary == "detail"
            with self.subTest(boundary=boundary):
                self._assert_main_blocks_without_private_artifact(runner, "VOLUME_POOL_IDENTITY_MISMATCH")

    def test_incus_pool_field_stays_unknown_at_both_real_boundaries(self) -> None:
        unexpected_pools: tuple[object, ...] = ("pool", "", None, False, 0, [], {})
        for boundary in ("list", "detail"):
            for unexpected_pool in unexpected_pools:
                runner = self._InventoryRunner()
                if boundary == "list":
                    runner.list_rows["volumes"] = [{"name": "web", "type": "container", "content_type": "filesystem",
                        "project": "alpha", "config": {}, "used_by": runner.volume_used_by, "pool": unexpected_pool}]
                else:
                    runner.detail_overrides["incus_storage_volume_show"] = {"pool": unexpected_pool}
                with self.subTest(boundary=boundary, pool=unexpected_pool), self.assertRaisesRegex(
                        inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
                    inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket",
                                                incus=True, before_query=lambda: None)

    def test_volume_detail_requires_explicit_family_and_preserves_existing_denials(self) -> None:
        volume: dict[str, object] = {"name": "data", "type": "custom", "content_type": "filesystem",
                                     "project": "alpha", "config": {}, "used_by": []}
        lxd_volume = {**volume, "pool": "pool"}
        self.assertEqual(inventory._validate_volume_show(lxd_volume, "pool", "custom", "data", "alpha", incus=False), lxd_volume)
        self.assertEqual(inventory._validate_volume_show(volume, "pool", "custom", "data", "alpha", incus=True), volume)
        invalid_changes: tuple[dict[str, object], ...] = (
            {"project": "foreign"}, {"project": None}, {"name": "foreign"}, {"type": "future"},
            {"config": []}, {"config": {"x": None}}, {"used_by": None}, {"used_by": ""},
            {"used_by": ["not-an-api-link"]}, {"created_at": 123}, {"unknown": "new"},
        )
        for incus in (False, True):
            base = volume if incus else lxd_volume
            for changes in invalid_changes:
                with self.subTest(incus=incus, changes=changes), self.assertRaises(inventory.InventoryError):
                    inventory._validate_volume_show({**base, **changes}, "pool", "custom", "data", "alpha", incus=incus)
            for missing_field in ("project", "config", "used_by"):
                incomplete = {key: value for key, value in base.items() if key != missing_field}
                with self.subTest(incus=incus, missing=missing_field), self.assertRaises(inventory.InventoryError):
                    inventory._validate_volume_show(incomplete, "pool", "custom", "data", "alpha", incus=incus)

    def test_valid_lxd_pool_never_weakens_owner_or_consumer_graph(self) -> None:
        cases = ("foreign_owner", "consumer_drift", "unresolved_consumer", "pool_reciprocity", "volume_reciprocity", "unknown_field", "content_type", "duplicate")
        for case in cases:
            runner = self._InventoryRunner()
            expected_code = "RESOURCE_SCHEMA_INVALID"
            if case == "foreign_owner":
                runner.volume_owner_project = "default"
                expected_code = "VOLUME_OWNER_PROJECT_UNSUPPORTED"
            elif case == "consumer_drift":
                runner.detail_overrides["lxd_storage_volume_show"] = {"used_by": []}
                expected_code = "VOLUME_CONSUMER_LIST_MISMATCH"
            elif case == "unresolved_consumer":
                runner.volume_used_by = ["/1.0/instances/missing?project=alpha"]
                expected_code = "VOLUME_CONSUMER_RECIPROCITY_MISMATCH"
            elif case == "pool_reciprocity":
                runner.pool_used_by = ["/1.0/storage-pools/pool/volumes/container/web?project=alpha"]
                expected_code = "POOL_CONSUMER_RECIPROCITY_MISMATCH"
            elif case == "volume_reciprocity":
                runner.volume_used_by = []
                expected_code = "VOLUME_CONSUMER_RECIPROCITY_MISMATCH"
            elif case == "unknown_field":
                runner.detail_overrides["lxd_storage_volume_show"] = {"unknown": "new"}
            elif case == "content_type":
                runner.detail_overrides["lxd_storage_volume_show"] = {"content_type": "future"}
                expected_code = "VOLUME_CONTENT_TYPE_UNSUPPORTED"
            else:
                volume_row = {"name": "web", "type": "container", "content_type": "filesystem",
                              "project": "alpha", "config": {}, "location": "none", "used_by": runner.volume_used_by}
                runner.list_rows["volumes"] = [dict(volume_row), dict(volume_row)]
                expected_code = "RESOURCE_DUPLICATE"
            with self.subTest(case=case):
                self._assert_main_blocks_without_private_artifact(runner, expected_code)

    def test_volume_list_created_at_must_be_a_string_when_present(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["volumes"] = [{"name": "web", "type": "container", "content_type": "filesystem",
                                        "project": "alpha", "description": "", "config": {},
                                        "created_at": 123, "used_by": runner.volume_used_by, "location": "none"}]
        with self.assertRaisesRegex(inventory.InventoryError, "RESOURCE_SCHEMA_INVALID"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def _assert_main_blocks_without_private_artifact(self, runner: _InventoryRunner, expected_code: str | None, *, incus: bool = False) -> bytes | None:
        active_unit = "incus.service" if incus else "lxd.service"
        active_service = inventory._unit_state(active_unit, {
            "LoadState": "loaded", "ActiveState": "active", "SubState": "running",
            "UnitFileState": "enabled", "MainPID": "4242"})
        missing_units = {
            unit: inventory._unit_state(unit, {
                "LoadState": "not-found", "ActiveState": "inactive", "SubState": "dead",
                "UnitFileState": "not-found", "MainPID": "0", **({"Listen": ""} if unit.endswith(".socket") else {})})
            for unit in inventory.UNITS if unit != active_unit
        }
        units = {active_unit: active_service, **missing_units}
        endpoints = {"/var/lib/lxd/unix.socket": ("lxd_system", not incus),
                     "/var/snap/lxd/common/lxd/unix.socket": ("lxd_snap", False),
                     "/var/lib/incus/unix.socket": ("incus_var_lib", False),
                     "/run/incus/unix.socket": ("incus_run", incus)}
        stderr = StringIO()
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "inventory.json"
            with patch.object(inventory, "Runner", return_value=runner), \
                    patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: units[unit]), \
                    patch.object(inventory, "_endpoint", side_effect=lambda _runner, path, unit="": endpoints[path]), \
                    patch.object(inventory, "_resolve_executable", return_value=("incus_system", "system:incus") if incus else ("lxd_system", "system:lxd")), \
                    patch.object(inventory, "_require_full_local_access"), \
                    patch.object(inventory, "_recheck_all"), \
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr), redirect_stdout(stdout):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(output)])
            self.assertFalse(output.exists())
            if expected_code is None:
                self.assertEqual(result, 0)
                self.assertEqual(stdout.getvalue(), "READ_ONLY_INVENTORY_COMPLETE\n")
                self.assertEqual(stderr.getvalue(), "")
                write.assert_called_once()
                return write.call_args.args[1]
            self.assertEqual(result, 2)
            self.assertEqual(stdout.getvalue(), "")
            write.assert_not_called()
            self.assertEqual(stderr.getvalue().strip(), f"BLOCKED:{expected_code}")
            return None

    def test_inherited_volume_detail_owner_blocks_main_before_private_artifact_write(self) -> None:
        runner = self._InventoryRunner()
        runner.volume_owner_project = "default"
        self._assert_main_blocks_without_private_artifact(runner, "VOLUME_OWNER_PROJECT_UNSUPPORTED")

    def test_inherited_volume_list_owner_blocks_main_before_private_artifact_write(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["volumes"] = [{"name": "web", "type": "container", "content_type": "filesystem",
                                        "project": "default", "description": "", "config": {},
                                        "created_at": "2026-10-01T00:00:00Z", "used_by": runner.volume_used_by,
                                        "location": "none"}]
        self._assert_main_blocks_without_private_artifact(runner, "VOLUME_OWNER_PROJECT_UNSUPPORTED")

    def test_profile_custom_disk_maps_to_typed_volume_consumer(self) -> None:
        devices = {"shared-data": {"type": "disk", "path": "/srv/data", "pool": "pool", "source": "data"}}
        self.assertEqual(
            inventory._volume_device_users(devices, "alpha", "profiles", "shared"),
            {("pool", "custom", "data"): {("profiles", "shared", "alpha")}},
        )

    def test_device_relationships_must_resolve_reciprocally(self) -> None:
        runner = self._InventoryRunner()
        runner.network_used_by = []
        with self.assertRaisesRegex(inventory.InventoryError, "NETWORK_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.pool_used_by = ["/1.0/storage-pools/pool/volumes/container/web?project=alpha"]
        with self.assertRaisesRegex(inventory.InventoryError, "POOL_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.volume_used_by = []
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_CONSUMER_RECIPROCITY_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.instance_network = "missing"
        with self.assertRaisesRegex(inventory.InventoryError, "NETWORK_DEVICE_REFERENCE_UNRESOLVED"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.instance_pool = "missing"
        with self.assertRaisesRegex(inventory.InventoryError, "STORAGE_ROOT_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.instance_custom_source = "missing"
        with self.assertRaisesRegex(inventory.InventoryError, "VOLUME_DEVICE_REFERENCE_UNRESOLVED"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_pool_consumer_volume_set_must_match_listed_volumes(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["volumes"] = []
        with self.assertRaisesRegex(inventory.InventoryError, "STORAGE_ROOT_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_list_and_detail_consumer_views_must_match(self) -> None:
        mismatched_rows: dict[str, list[dict[str, Any]]] = {
            "projects": [{"name": "alpha", "description": "", "config": {"features.networks": "true", "features.profiles": "true"},
                          "used_by": ["/1.0/profiles/bravo?project=alpha"]}],
            "profiles": [{"name": "bravo", "project": "alpha", "description": "", "config": {},
                          "devices": {"root": {"type": "disk", "path": "/", "pool": "pool"}, "eth0": {"type": "nic", "network": "net"}}, "used_by": []}],
            "networks": [{"name": "net", "project": "alpha", "type": "bridge", "managed": True,
                          "status": "Created", "config": {}, "description": "", "used_by": [], "locations": []}],
            "pools": [{"name": "pool", "project": "alpha", "driver": "dir", "config": {},
                       "description": "", "used_by": ["/1.0/profiles/bravo?project=alpha"],
                       "status": "Created", "locations": []}],
            "volumes": [{"name": "web", "type": "container", "content_type": "filesystem",
                         "project": "alpha", "description": "", "used_by": [], "location": "none"}],
        }
        expected_errors = {"projects": "PROJECT_CONSUMER_LIST_MISMATCH",
                           "profiles": "PROFILE_CONSUMER_LIST_MISMATCH",
                           "networks": "NETWORK_CONSUMER_LIST_MISMATCH",
                           "pools": "POOL_CONSUMER_LIST_MISMATCH",
                           "volumes": "VOLUME_CONSUMER_LIST_MISMATCH"}
        for resource, rows in mismatched_rows.items():
            with self.subTest(resource=resource):
                runner = self._InventoryRunner()
                runner.list_rows[resource] = rows
                with self.assertRaisesRegex(inventory.InventoryError, expected_errors[resource]):
                    inventory._inventory_client(
                        runner, "incus_system", "/run/incus/unix.socket", incus=True,
                        before_query=lambda: None)

    def test_local_socket_access_requires_full_administrator_group(self) -> None:
        with patch.object(inventory.os, "geteuid", return_value=1000), \
                patch.object(inventory.os, "getegid", return_value=1000), \
                patch.object(inventory.os, "getgroups", return_value=[1000]), \
                patch.object(inventory.os, "stat", return_value=Mock(st_gid=2000)), \
                patch.object(inventory.grp, "getgrgid", return_value=Mock(gr_name="incus")):
            with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_ACCESS_SCOPE_UNPROVEN"):
                inventory._require_full_local_access("/run/incus/unix.socket", incus=True)

        with patch.object(inventory.os, "geteuid", return_value=1000), \
                patch.object(inventory.os, "getegid", return_value=1000), \
                patch.object(inventory.os, "getgroups", return_value=[1000, 2000]), \
                patch.object(inventory.os, "stat", return_value=Mock(st_gid=2000)), \
                patch.object(inventory.grp, "getgrgid", return_value=Mock(gr_name="incus-admin")):
            inventory._require_full_local_access("/run/incus/unix.socket", incus=True)

    def test_standard_extended_cli_list_rows_are_accepted_but_unknown_fields_are_rejected(self) -> None:
        runner = self._InventoryRunner()
        _version, projects = inventory._inventory_client(
            runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)
        instance = projects[0]["instances"][0]
        self.assertEqual(instance["name"], "web")
        self.assertEqual(instance["status"], "Running")
        self.assertNotIn("expanded_config", instance)
        self.assertNotIn("last_used_at", instance)
        self.assertNotIn("10GiB", str(projects))

        standard_rows = {
            "projects": {"name": "alpha", "unexpected": "value"},
            "profiles": {"name": "zeta", "unexpected": "value"},
            "instances": {"name": "web", "unexpected": "value"},
            "networks": {"name": "net", "unexpected": "value"},
            "pools": {"name": "pool", "unexpected": "value"},
            "volumes": {"name": "web", "unexpected": "value"},
        }
        for resource, row in standard_rows.items():
            with self.subTest(resource=resource):
                bad_runner = self._InventoryRunner()
                bad_runner.list_rows[resource] = [row]
                with self.assertRaises(inventory.InventoryError):
                    inventory._inventory_client(
                        bad_runner, "incus_system", "/run/incus/unix.socket", incus=True,
                        before_query=lambda: None)

    def test_instance_profiles_must_be_present_and_match_detail_responses(self) -> None:
        runner = self._InventoryRunner()
        runner.list_rows["instances"] = [{
            "name": "web", "project": "alpha", "architecture": "x86_64", "config": {}, "devices": {},
            "ephemeral": False, "expanded_config": {}, "expanded_devices": {}, "stateful": False,
            "status": "Running", "status_code": 103, "type": "container", "location": "none",
            "description": "", "created_at": "2026-10-01T00:00:00Z", "last_used_at": "2026-10-02T00:00:00Z",
        }]
        with self.assertRaises(inventory.InventoryError):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

        runner = self._InventoryRunner()
        runner.detail_profiles = ["different"]
        with self.assertRaisesRegex(inventory.InventoryError, "INSTANCE_PROFILE_LIST_MISMATCH"):
            inventory._inventory_client(
                runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_artifact_schema_size_and_redaction_are_enforced(self) -> None:
        artifact = self._valid_artifact()
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))
        rows = self._network_rows()
        self._bind_artifact(artifact, rows, incus=True)
        self.assertTrue(inventory._validate_artifact(artifact).endswith(b"\n"))
        malformed_volume = self._valid_artifact()
        malformed_volume["lxd_projects"] = [{"project": "alpha", "features_networks": True, "features_profiles": True,
                                     "effective_network_project": "alpha", "profiles": [], "instances": [], "networks": [],
                                              "pools": [{"name": "pool", "type": "dir", "used_by": [],
                                                         "volumes": [{"name": "web", "type": "container",
                                                                      "content_type": "filesystem", "used_by": [],
                                                                      "config": {}}]}]}]
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact(malformed_volume)
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "unexpected": "field"})
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "lxd_projects": [{"path": "/var/lib/lxd"}]})
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact({**artifact, "target_host": "192.168.178.33"})
        malformed = self._valid_artifact()
        malformed["lxd_units"][0]["active_state"] = "active"
        with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_UNIT_STATE_INVALID"):
            inventory._validate_artifact(malformed)
        malformed = self._valid_artifact()
        malformed["incus_units"][0]["main_pid"] = True
        with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_UNIT_VALUE_INVALID"):
            inventory._validate_artifact(malformed)

    def test_output_has_no_raw_argv_or_endpoint_paths_in_command_records(self) -> None:
        runner = inventory.Runner(popen=Mock())
        runner.records.append({"command_id": "socket_exists", "safe_args": ["default"],
                              "exit_status": 0, "stdout_bytes": 10, "stderr_bytes": 0})
        artifact = self._valid_artifact(runner.records)
        raw = inventory._validate_artifact(artifact).decode()
        for forbidden in ("argv", "/var/lib/lxd", "/proc/", "https://", "/snap/lxd"):
            self.assertNotIn(forbidden, raw)

    def test_artifact_preserves_typed_project_scoped_consumer_references(self) -> None:
        artifact = self._network_artifact()
        encoded = inventory._validate_artifact(artifact)
        self.assertIn(b'"kind":"instances","name":"web","project":"alpha"', encoded)
        malformed = copy.deepcopy(artifact)
        malformed["incus_projects"][0]["networks"][2]["used_by"][0].pop("project")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_artifact(malformed)

    def test_network_schema_two_keeps_unmanaged_interfaces_and_default_last(self) -> None:
        for incus in (False, True):
            with self.subTest(incus=incus):
                runner = self._NetworkRunner()
                rows = self._network_rows(runner, incus=incus)
                self.assertEqual(list(runner.configs), ["alpha", "default"])
                self.assertEqual([row["project"] for row in rows], ["alpha", "default"])
                for row in rows:
                    self.assertEqual(row["effective_network_project"], "default")
                    self.assertEqual([net["name"] for net in row["networks"]], ["eth0", "lo", "net"])
                    self.assertEqual([net["owner_project"] for net in row["networks"]], [None, None, "default"])
                    self.assertEqual([net["managed"] for net in row["networks"]], [False, False, True])
                self.assertEqual(rows[0]["networks"], rows[1]["networks"])
                self.assertTrue(all(call[0][2] in {"version", "project", "profile", "query", "network", "storage"}
                                    for call in runner.calls))
                artifact = self._valid_artifact()
                self._bind_artifact(artifact, rows, incus=incus)
                encoded = inventory._validate_artifact(artifact)
                self.assertEqual(json.loads(encoded)["schema_version"], 4)
                self.assertNotIn(b'"config":', encoded)

    def test_network_empty_status_is_explicitly_unmanaged_only(self) -> None:
        row = self._NetworkRunner.network("eth0", False, "physical")
        for valid_status in ("", "Created"):
            self.assertEqual(inventory._validate_network_show({**row, "status": valid_status}, "eth0", "default")["status"], valid_status)
        for managed, status in ((True, ""), (None, ""), (0, ""), ("false", ""), (False, None), (False, 0), (False, False)):
            with self.subTest(managed=managed, status=status), self.assertRaises(inventory.InventoryError):
                inventory._validate_network_show({**row, "managed": managed, "status": status}, "eth0", "default")
        missing = dict(row)
        missing.pop("managed")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_network_show(missing, "eth0", "default")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_pool_show({"name": "pool", "driver": "dir", "config": {}, "used_by": [], "status": ""}, "pool", "default")
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_list_metadata({"type": "container", "status": ""}, "default")

    def test_network_metadata_drift_and_family_project_binding(self) -> None:
        for field, value in (("managed", False), ("type", "physical"), ("config", {"user.changed": "yes"})):
            runner = self._NetworkRunner()
            def change(project, kind, row):
                if project == "alpha" and kind == "networks" and row["name"] == "net":
                    row[field] = value
            runner.detail_mutation = change
            with self.subTest(field=field), self.assertRaisesRegex(inventory.InventoryError, "NETWORK_METADATA_LIST_MISMATCH"):
                self._network_rows(runner)
        for incus in (True, False):
            runner = self._NetworkRunner()
            runner.project_override = lambda _argv, project: ("alpha" if incus else "default") if project == "alpha" else "default"
            with self.subTest(incus=incus), self.assertRaises(inventory.InventoryError):
                self._network_rows(runner, incus=incus)

    def test_network_feature_values_and_explicit_unsupported_project_boundaries(self) -> None:
        runner = self._NetworkRunner()
        runner.configs["alpha"]["features.networks"] = "true"
        with self.assertRaisesRegex(inventory.InventoryError, "UNMANAGED_NETWORK_SCOPE_INVALID"):
            self._network_rows(runner)
        runner = self._NetworkRunner()
        runner.configs["alpha"].pop("features.networks")
        self.assertIsNone(self._network_rows(runner)[0]["features_networks"])
        for flag in (None, "false", "true"):
            config: dict[str, Any] = {"features.profiles": "true"}
            if flag is not None:
                config["features.networks"] = flag
            self.assertEqual(inventory._project_network_flags(config, "alpha")[2], "alpha" if flag == "true" else "default")
            self.assertEqual(inventory._project_network_flags(config, "default")[2], "default")
        for key in ("features.networks", "features.profiles", "restricted"):
            for value in ("", "TRUE", "1", " false", "false\n", True):
                config = {"features.profiles": "true", key: value}
                with self.subTest(key=key, value=value), self.assertRaises(inventory.InventoryError):
                    inventory._project_network_flags(config, "alpha")
        for config, code in (({"features.profiles": "true", "restricted": "true"}, "PROJECT_NETWORK_RESTRICTIONS_UNSUPPORTED"),
                             ({"features.profiles": "true", "restricted.devices.nic": "managed"}, "PROJECT_NETWORK_RESTRICTIONS_UNSUPPORTED"),
                             ({"features.profiles": "true", "restricted.networks.access": "net"}, "PROJECT_NETWORK_RESTRICTIONS_UNSUPPORTED")):
            with self.subTest(config=config), self.assertRaisesRegex(inventory.InventoryError, code):
                inventory._project_network_flags(config, "alpha")
        runner = self._NetworkRunner()
        runner.detail_mutation = lambda project, kind, row: row.update(config={"features.profiles": "true"}) if project == "alpha" and kind == "projects" else None
        with self.assertRaisesRegex(inventory.InventoryError, "PROJECT_CONFIGURATION_DRIFT"):
            self._network_rows(runner)

    def test_inherited_network_missing_default_and_view_drift_fail_closed(self) -> None:
        cases = ("missing_default", "missing_row", "extra_row", "duplicate", "managed", "config", "consumers")
        for case in cases:
            runner = self._NetworkRunner()
            if case == "missing_default":
                del runner.configs["default"]
            elif case == "missing_row":
                runner.networks["alpha"].pop(0)
            elif case == "extra_row":
                runner.networks["alpha"].append(runner.network("extra", False))
            elif case == "duplicate":
                runner.networks["default"].append(runner.network("net", True))
            elif case == "managed":
                runner.networks["alpha"][0]["managed"] = True
                runner.networks["alpha"][0]["status"] = "Created"
            elif case == "config":
                runner.networks["alpha"][2]["config"] = {"user.drift": "x"}
            else:
                def change(project, rows):
                    if project == "alpha":
                        rows[2]["used_by"] = rows[2]["used_by"][:1]
                runner.list_mutation = change
                def detail_change(project, kind, row):
                    if project == "alpha" and kind == "networks" and row["name"] == "net":
                        row["used_by"] = row["used_by"][:1]
                runner.detail_mutation = detail_change
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                self._network_rows(runner)

    def test_project_membership_never_claims_unmanaged_or_inherited_networks(self) -> None:
        for project, name in (("alpha", "net"), ("default", "eth0")):
            runner = self._NetworkRunner()
            runner.project_links = lambda current, links: links + ["/1.0/networks/" + name + "?project=" + project] if current == project else links
            with self.subTest(project=project, name=name), self.assertRaisesRegex(inventory.InventoryError, "PROJECT_CONSUMER_RECIPROCITY_MISMATCH"):
                self._network_rows(runner)

    def test_expanded_nics_override_local_and_keep_profile_consumer(self) -> None:
        runner = self._NetworkRunner()
        runner.local_devices["alpha"] = {"stale": {"type": "nic", "network": "missing", "vlan": "123"}}
        runner.expanded_devices["alpha"] = {"eth0": {"type": "nic", "parent": "eth0"},
                                            "eth1": {"type": "nic", "parent": "eth0"}}
        runner.network_users["net"] = ["/1.0/profiles/profile?project=alpha"]
        runner.network_users["eth0"] = ["/1.0/instances/web?project=alpha", "/1.0/instances/web?project=alpha"]
        rows = self._network_rows(runner)
        instance = rows[0]["instances"][0]
        self.assertEqual(instance["network_refs"], [{"project": "default", "name": "eth0"}])
        self.assertEqual(rows[0]["profiles"][0]["network_refs"], [{"project": "default", "name": "net"}])
        self.assertEqual(len(rows[1]["networks"][0]["used_by"]), 1)
        artifact = self._valid_artifact()
        self._bind_artifact(artifact, rows, incus=True)
        inventory._validate_artifact(artifact)
        runner.expanded_devices["alpha"]["eth2"] = {"type": "nic", "network": "net"}
        runner.network_users["net"].append("/1.0/instances/web?project=alpha")
        rows = self._network_rows(runner)
        self.assertEqual(len(rows[0]["instances"][0]["network_refs"]), 2)

    def test_literal_parent_support_and_named_unsupported_nic_boundaries(self) -> None:
        for parent in ("eth0", "net"):
            runner = self._NetworkRunner()
            runner.profile_devices["alpha"] = {"eth0": {"type": "nic", "parent": parent}}
            runner.expanded_devices["alpha"] = copy.deepcopy(runner.profile_devices["alpha"])
            runner.network_users[parent] = runner.network_users.pop("net") if parent != "net" else runner.network_users["net"]
            self.assertEqual(self._network_rows(runner)[0]["profiles"][0]["network_refs"][0]["name"], parent)
        for device, code in (({"network":
            "net", "vlan": "123"}, "NETWORK_VLAN_UNSUPPORTED"),
                             ({"parent": "eth0", "vlan": "123"}, "NETWORK_VLAN_UNSUPPORTED"),
                             ({"network": "net", "parent": "net"}, "NETWORK_DEVICE_AMBIGUOUS"),
                             ({"parent": "lo"}, "NETWORK_LOOPBACK_CONSUMER_UNSUPPORTED"),
                             ({"parent": "missing"}, "NETWORK_DEVICE_REFERENCE_UNRESOLVED"),
                             ({"network": "eth0"}, "NETWORK_MANAGED_REFERENCE_REQUIRED")):
            runner = self._NetworkRunner()
            runner.profile_devices["alpha"] = {"eth0": {"type": "nic", **device}}
            with self.subTest(device=device), self.assertRaisesRegex(inventory.InventoryError, code):
                self._network_rows(runner)
        runner = self._NetworkRunner()
        runner.profile_devices["alpha"] = {"eth0": {"type": "nic", "parent": "net"}}
        for rows in runner.networks.values():
            rows[2]["type"] = "ovn"
        with self.assertRaisesRegex(inventory.InventoryError, "NETWORK_OVN_PARENT_UNSUPPORTED"):
            self._network_rows(runner)
        for kind in ("disk", "proxy"):
            for vlan in ("", "1"):
                with self.subTest(kind=kind, vlan=vlan), self.assertRaises(inventory.InventoryError):
                    inventory._devices({"device": {"type": kind, "vlan": vlan}})

    def test_network_uplinks_peer_and_other_consumer_kinds_fail_explicitly(self) -> None:
        for config in ({"network":
            "net"}, {"parent": "eth0"}):
            runner = self._NetworkRunner()
            for rows in runner.networks.values():
                rows[2]["config"] = config
            with self.subTest(config=config), self.assertRaisesRegex(inventory.InventoryError, "NETWORK_UPLINK_UNSUPPORTED"):
                self._network_rows(runner)
        for link, code in (("/1.0/networks/net", "NETWORK_PEERING_OR_DEPENDENCY_UNSUPPORTED"),
                           ("/1.0/storage-pools/pool", "NETWORK_CONSUMER_KIND_UNSUPPORTED")):
            runner = self._NetworkRunner()
            runner.network_users["net"].append(link)
            with self.subTest(link=link), self.assertRaisesRegex(inventory.InventoryError, code):
                self._network_rows(runner)

    def test_network_default_consumer_urls_and_distinct_project_scopes(self) -> None:
        runner = self._NetworkRunner()
        runner.default_profile = True
        runner.profile_devices["default"] = {"eth0": {"type": "nic", "network": "net"}}
        runner.network_users["net"].append("/1.0/profiles/profile")
        rows = self._network_rows(runner)
        self.assertIn({"kind": "profiles", "name": "profile", "project": "default"}, rows[0]["networks"][2]["used_by"])
        artifact = self._valid_artifact()
        self._bind_artifact(artifact, rows, incus=True)
        inventory._validate_artifact(artifact)
        runner = self._NetworkRunner()
        # An omitted project must resolve to default, never the requesting alpha view.
        runner.network_users["net"].append("/1.0/profiles/missing")
        with self.assertRaisesRegex(inventory.InventoryError, "NETWORK_CONSUMER_RECIPROCITY_MISMATCH"):
            self._network_rows(runner)
        for incus in (False, True):
            runner = self._NetworkRunner()
            runner.configs["alpha"]["features.networks"] = "true"
            runner.networks["alpha"] = [runner.network("net", True)]
            # Separate scopes expose separate complete consumer sets.
            def list_users(project, rows):
                if project == "default":
                    for row in rows:
                        row["used_by"] = []
            runner.list_mutation = list_users
            def detail_users(project, kind, row):
                if project == "default" and kind == "networks":
                    row["used_by"] = []
            runner.detail_mutation = detail_users
            rows = self._network_rows(runner, incus=incus)
            self.assertEqual(rows[0]["networks"][0]["owner_project"], "alpha")
            self.assertEqual(rows[1]["networks"][2]["used_by"], [])

    def test_schema_two_independently_rejects_scope_owner_and_edge_tampering(self) -> None:
        artifact = self._network_artifact()
        self.assertEqual(json.loads(inventory._validate_artifact(artifact)), artifact)
        for case in ("schema1", "missing_managed", "bool_managed", "unmanaged_owner", "wrong_owner", "scope", "flags", "missing_default", "duplicate", "config_digest", "consumer", "no_nic", "only_local_nic", "excess_refs", "duplicate_nics", "duplicate_refs", "missing_refs", "peer"):
            value = copy.deepcopy(artifact)
            projects = value["incus_projects"]
            alpha, default = projects
            if case == "schema1":
                value["schema_version"] = 1
            elif case == "missing_managed":
                alpha["networks"][0].pop("managed")
            elif case == "bool_managed":
                alpha["networks"][0]["managed"] = 0
            elif case == "unmanaged_owner":
                alpha["networks"][0]["owner_project"] = "default"
            elif case == "wrong_owner":
                alpha["networks"][2]["owner_project"] = "alpha"
            elif case == "scope":
                alpha["effective_network_project"] = "alpha"
            elif case == "flags":
                alpha["features_networks"] = "false"
            elif case == "missing_default":
                projects.pop()
            elif case == "duplicate":
                default["networks"].append(copy.deepcopy(default["networks"][0]))
            elif case == "config_digest":
                alpha["networks"][2]["config_digest"] = "a" * 64
            elif case == "consumer":
                for project in projects:
                    project["networks"][2]["used_by"].pop()
            elif case == "no_nic":
                alpha["profiles"][0]["devices"] = []
            elif case == "only_local_nic":
                alpha["instances"][0]["local_devices"] = alpha["instances"][0]["expanded_devices"]
                alpha["instances"][0]["expanded_devices"] = []
            elif case == "excess_refs":
                alpha["instances"][0]["network_refs"].insert(0, {"project": "default", "name": "eth0"})
            elif case == "duplicate_nics":
                alpha["instances"][0]["expanded_devices"] *= 2
            elif case == "duplicate_refs":
                alpha["instances"][0]["network_refs"] *= 2
            elif case == "missing_refs":
                alpha["instances"][0]["network_refs"] = []
            else:
                for project in projects:
                    project["networks"][2]["used_by"].insert(1, {"kind": "networks", "name": "net", "project": "default"})
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                inventory._validate_artifact(value)

    def test_server_root_fixed_command_rejects_method_uri_arity_and_phase_before_spawn(self) -> None:
        popen = Mock()
        runner = inventory.Runner(popen=popen)
        base = ["/usr/bin/lxc", "--force-local", "query", "--request", "GET", "--raw", "/1.0"]
        mutations = [base[:4] + ["POST"] + base[5:], base[:-1] + ["/1.0?target=other"],
                     base[:-1] + ["/1.0/projects"], base + ["extra"], base[:1] + base[2:]]
        for argv in mutations:
            with self.subTest(argv=argv), self.assertRaises(inventory.InventoryError):
                runner.run(argv, env={**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"},
                           command_id="lxd_server_root_initial", safe_args=[])
        for names, project in ((("extra",), "default"), ((), "other")):
            with self.subTest(names=names, project=project), self.assertRaises(inventory.InventoryError):
                inventory._detail(runner, ["/usr/bin/lxc", "--force-local"], "server-root", names, project,
                    command_id="lxd_server_root_initial", env={**inventory.ENV_BASE, "LXD_SOCKET": "/var/lib/lxd/unix.socket"}, safe_args=[])
        before = Mock()
        with self.assertRaises(inventory.InventoryError):
            inventory._read_server_root(runner, ["/usr/bin/lxc", "--force-local"], {}, before,
                                        incus=False, cli_version="5.21.9", phase="other")
        before.assert_not_called()
        popen.assert_not_called()

    def test_root_admission_full_family_dtos_and_discarded_nil_metadata(self) -> None:
        for incus in (False, True):
            fixture = self._InventoryRunner()
            metadata = fixture.server_row(incus)
            observed = inventory._validate_server_root(metadata, incus=incus, cli_version="6.0.5")
            self.assertIs(observed["server_clustered"], False)
            self.assertEqual(observed["server"], "incus" if incus else "lxd")
            for field in ("addresses", "architectures", "kernel_features", "lxc_features", "storage_supported_drivers"):
                nullable = copy.deepcopy(metadata)
                nullable["environment"][field] = None
                inventory._validate_server_root(nullable, incus=incus, cli_version="6.0.5")
            if not incus:
                metadata["config"] = {"hidden.secret": True, "user.visible": "text"}
                inventory._validate_server_root(metadata, incus=False, cli_version="6.0.5")
            malformed_config_values: tuple[object, ...] = (False, 0, 1.0, [], {}, None)
            for invalid in malformed_config_values + ((True,) if incus else ()):
                malformed = copy.deepcopy(metadata)
                malformed["config"] = {"invalid": invalid}
                with self.subTest(incus=incus, invalid=invalid), self.assertRaises(inventory.InventoryError):
                    inventory._validate_server_root(malformed, incus=incus, cli_version="6.0.5")
            for case in ("missing", "unknown", "cross_family", "nested_lowercase", "nested_bool_int", "null_config", "null_environment"):
                malformed = copy.deepcopy(metadata)
                if case == "missing":
                    malformed["environment"].pop("server_clustered")
                elif case == "unknown":
                    malformed["environment"]["unexpected"] = "x"
                elif case == "cross_family":
                    if incus:
                        malformed["client_certificate"] = False
                    else:
                        malformed.pop("client_certificate")
                elif case == "nested_lowercase":
                    malformed["environment"]["storage_supported_drivers"] = [{"name": "dir", "Version": "1", "Remote": False}]
                elif case == "nested_bool_int":
                    malformed["environment"]["storage_supported_drivers"][0]["Remote"] = 0
                elif case == "null_config":
                    malformed["config"] = None
                else:
                    malformed["environment"] = None
                with self.subTest(incus=incus, case=case), self.assertRaises(inventory.InventoryError):
                    inventory._validate_server_root(malformed, incus=incus, cli_version="6.0.5")

    def test_initial_and_final_admission_fail_closed_without_private_writer(self) -> None:
        invalid_clustered: tuple[object, ...] = (None, True, 0, 1, "false", [], {})
        for phase in ("initial", "final"):
            for invalid_cluster in invalid_clustered:
                runner = self._InventoryRunner()
                environment = runner.server_row(False)["environment"]
                environment["server_clustered"] = invalid_cluster
                runner.detail_overrides["lxd_server_root_" + phase] = {"environment": environment}
                code = "SERVER_ADMISSION_BLOCKED" if invalid_cluster is True else "SERVER_SCHEMA_INVALID"
                with self.subTest(phase=phase, clustered=invalid_cluster):
                    self._assert_main_blocks_without_private_artifact(runner, code)
                    ids = [call[2] for call in runner.calls]
                    self.assertEqual("lxd_project_list" in ids, phase == "final")
        for changes in ({"auth": "untrusted"}, {"public": True}, {"api_version": "other"}, {"api_status": "devel"}):
            runner = self._InventoryRunner()
            runner.detail_overrides["lxd_server_root_initial"] = changes
            self._assert_main_blocks_without_private_artifact(runner, "SERVER_ADMISSION_BLOCKED")
        for field, invalid_value in (("server", "other"), ("project", "alpha"), ("server_version", "9.9.9")):
            runner = self._InventoryRunner()
            environment = runner.server_row(False)["environment"]
            environment[field] = invalid_value
            runner.detail_overrides["lxd_server_root_final"] = {"environment": environment}
            self._assert_main_blocks_without_private_artifact(runner, "SERVER_ADMISSION_BLOCKED")

    def test_server_proof_guard_and_final_budget_failure_propagate_without_artifact(self) -> None:
        runner = self._InventoryRunner()
        before = Mock(side_effect=inventory.InventoryError("RUNTIME_UNIT_DRIFT"))
        with self.assertRaisesRegex(inventory.InventoryError, "RUNTIME_UNIT_DRIFT"):
            inventory._read_server_root(runner, ["/usr/bin/lxc", "--force-local"], {}, before,
                                        incus=False, cli_version="6.0.5", phase="initial")
        self.assertEqual(runner.calls, [])
        class FinalBudgetRunner(NativeRuntimeInventoryTests._InventoryRunner):
            def run(self, argv, **kwargs):
                if kwargs["command_id"] == "lxd_server_root_final":
                    raise inventory.InventoryError("INVENTORY_BUDGET_EXCEEDED")
                return super().run(argv, **kwargs)
        self._assert_main_blocks_without_private_artifact(FinalBudgetRunner(), "INVENTORY_BUDGET_EXCEEDED")

    def test_root_secret_canaries_are_never_persisted_or_reported(self) -> None:
        runner = self._InventoryRunner()
        metadata = runner.server_row(False)
        canary = "secret-canary-must-stay-in-memory"
        metadata["config"] = {"user.private": canary}
        metadata["auth_user_name"] = canary
        for field in ("certificate", "addresses", "server_name"):
            metadata["environment"][field] = [canary] if field == "addresses" else canary
        with patch.object(runner, "server_row", return_value=metadata):
            proof: dict[str, Any] = {}
            _, rows = inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket", incus=False,
                                                  before_query=lambda: None, proof=proof)
        artifact = self._valid_artifact()
        self._bind_artifact(artifact, rows, incus=False)
        artifact["lxd_admission"] = proof["admission"]
        encoded = inventory._validate_artifact(artifact).decode()
        self.assertNotIn(canary, encoded)
        self.assertNotIn("certificate", encoded)
        runner = self._InventoryRunner()
        with patch.object(runner, "server_row", return_value=metadata):
            raw = self._assert_main_blocks_without_private_artifact(runner, None)
        self.assertIsInstance(raw, bytes)
        self.assertNotIn(canary.encode(), raw or b"")
        self.assertNotIn(canary, json.dumps(runner.records))
        runner = self._InventoryRunner()
        metadata["environment"]["server_clustered"] = True
        with patch.object(runner, "server_row", return_value=metadata):
            self._assert_main_blocks_without_private_artifact(runner, "SERVER_ADMISSION_BLOCKED")

    def test_active_default_completeness_capture_and_reader_inactive_positive(self) -> None:
        inventory._validate_artifact(self._valid_artifact())
        for empty in (False, True):
            runner = self._InventoryRunner()
            runner.omit_default_project = True
            if empty:
                runner.list_rows["projects"] = []
            with self.subTest(empty=empty):
                self._assert_main_blocks_without_private_artifact(runner, "PROJECT_DEFAULT_MISSING")
                self.assertNotIn("lxd_project_show", [call[2] for call in runner.calls])
            artifact = self._network_artifact()
            artifact["incus_projects"] = [] if empty else artifact["incus_projects"][:1]
            artifact["incus_pools"] = inventory._canonical_pools(artifact["incus_projects"])
            with self.assertRaises(inventory.InventoryError):
                inventory._validate_artifact(artifact)
        runner = self._InventoryRunner()
        runner.list_rows["projects"] = [{"name": "default", "config": {}, "used_by": []}]
        self._assert_main_blocks_without_private_artifact(runner, "PROJECT_DUPLICATE")

    def test_storage_root_pool_users_differ_from_project_volume_users(self) -> None:
        runner = self._InventoryRunner()
        proof: dict[str, Any] = {}
        _, rows = inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket", incus=False,
                                              before_query=lambda: None, proof=proof)
        users = rows[0]["pools"][0]["used_by"]
        self.assertEqual(users, [{"kind": "instances", "name": "web", "project": "alpha"},
                                 {"kind": "profiles", "name": "bravo", "project": "alpha"}])
        self.assertIn({"kind": "storage-volumes", "name": "pool/container/web", "project": "alpha"}, rows[0]["used_by"])
        self.assertEqual(rows[1]["pools"][0]["used_by"], users)
        self.assertEqual(set(proof["admission"]), {"initial", "final"})
        self.assertEqual([call[2] for call in runner.calls if "server_root" in call[2]],
                         ["lxd_server_root_initial", "lxd_server_root_final"])

    def test_storage_custom_api_and_effective_projections_stay_distinct(self) -> None:
        runner = self._NetworkRunner()
        runner.configs["alpha"]["features.storage.volumes"] = "true"
        runner.storage_pools.append("data")
        runner.storage_volumes[("alpha", "data")] = [{"name": "shared", "type": "custom", "content_type": "filesystem",
            "project": "alpha", "config": {}, "location": "none", "used_by": ["/1.0/profiles/profile?project=alpha"]},
            {"name": "unused", "type": "custom", "content_type": "filesystem", "project": "alpha", "config": {}, "location": "none", "used_by": []}]
        runner.profile_devices["alpha"]["data"] = {"type": "disk", "path": "/data", "pool": "data", "source": "shared"}
        runner.expanded_devices["alpha"]["data"] = dict(runner.profile_devices["alpha"]["data"])
        # A profile-inherited device has no same-name local entry; devices are not property-merged.
        rows = self._network_rows(runner)
        instance = rows[0]["instances"][0]
        self.assertEqual(instance["api_storage_devices"], [])
        self.assertEqual([entry["source"] for entry in instance["effective_storage_devices"] if entry["selector"] == "custom"], ["shared"])
        data_pool = next(pool for pool in rows[0]["pools"] if pool["name"] == "data")
        self.assertNotIn({"kind": "instances", "name": "web", "project": "alpha"}, data_pool["used_by"])
        self.assertEqual(len(data_pool["volumes"]), 2)
        runner.local_devices["alpha"]["data"] = dict(runner.expanded_devices["alpha"]["data"])
        runner.storage_volumes[("alpha", "data")][0]["used_by"].append("/1.0/instances/web?project=alpha")
        rows = self._network_rows(runner)
        self.assertEqual(rows[0]["instances"][0]["api_storage_devices"][0]["source"], "shared")
        # A complete local override replaces the whole inherited device; raw profile remains a user.
        runner.local_devices["alpha"]["data"]["source"] = "unused"
        runner.expanded_devices["alpha"]["data"] = dict(runner.local_devices["alpha"]["data"])
        runner.storage_volumes[("alpha", "data")][0]["used_by"].remove("/1.0/instances/web?project=alpha")
        runner.storage_volumes[("alpha", "data")][1]["used_by"].append("/1.0/instances/web?project=alpha")
        rows = self._network_rows(runner)
        effective = rows[0]["instances"][0]["effective_storage_devices"]
        self.assertEqual([entry["source"] for entry in effective if entry["selector"] == "custom"], ["unused"])

    def test_global_storage_two_projects_and_vm_root_identity(self) -> None:
        runner = self._NetworkRunner()
        runner.default_profile = True
        runner.instance_projects.add("default")
        runner.storage_volumes[("default", "pool")] = [{"name": "web", "type": "container", "content_type": "filesystem",
            "project": "default", "config": {}, "location": "none", "used_by": ["/1.0/instances/web"]}]
        rows = self._network_rows(runner)
        self.assertIn({"kind": "instances", "name": "web", "project": "default"}, rows[0]["pools"][0]["used_by"])
        for incus in (False, True):
            vm = self._NetworkRunner()
            vm.storage_volumes[("alpha", "pool")][0].update(type="virtual-machine", content_type="block")
            def vm_type(project, kind, row):
                if project == "alpha" and kind == "instances":
                    row["type"] = "virtual-machine"
            vm.detail_mutation = vm_type
            # List and detail share the same actual instance DTO factory.
            original = vm.instance_row
            with patch.object(vm, "instance_row", side_effect=lambda project: {**original(project), "type": "virtual-machine"}):
                self.assertEqual(self._network_rows(vm, incus=incus)[0]["pools"][0]["volumes"][0]["used_by"],
                                 [{"kind": "instances", "name": "web", "project": "alpha"}])

    def test_storage_graph_named_unsupported_and_identity_boundaries(self) -> None:
        for link, code in (("/1.0/images/image", "STORAGE_IMAGE_UNSUPPORTED"),
                           ("/1.0/instances/web/snapshots/snap", "STORAGE_SNAPSHOT_OR_SELECTOR_UNSUPPORTED"),
                           ("/1.0/storage-pools/pool/buckets/bucket", "STORAGE_BUCKET_UNSUPPORTED"),
                           ("/1.0/instances/web?target=member", "STORAGE_MEMBER_SCOPE_UNSUPPORTED"),
                           ("/1.0", "STORAGE_DAEMON_CONSUMER_UNSUPPORTED")):
            with self.subTest(link=link), self.assertRaisesRegex(inventory.InventoryError, code):
                inventory._storage_consumer_refs([link], "alpha")
        for selector in ("source.type", "source.snapshot"):
            with self.assertRaisesRegex(inventory.InventoryError, "STORAGE_SNAPSHOT_OR_SELECTOR_UNSUPPORTED"):
                inventory._devices({"disk": {"type": "disk", selector: ""}})
        for case in ("root_pool", "root_type", "orphan", "content", "location", "missing_root", "shared_custom", "source_subpath", "url_default"):
            runner = self._NetworkRunner()
            if case == "root_pool":
                runner.root_pools["alpha"] = "missing"
            elif case == "root_type":
                runner.storage_volumes[("alpha", "pool")][0]["type"] = "virtual-machine"
            elif case == "orphan":
                runner.storage_volumes[("alpha", "pool")][0]["name"] = "other"
            elif case == "content":
                runner.storage_volumes[("alpha", "pool")][0]["content_type"] = "block"
            elif case == "location":
                runner.storage_volumes[("alpha", "pool")][0]["location"] = ""
            elif case == "missing_root":
                runner.storage_volumes[("alpha", "pool")] = []
            elif case == "shared_custom":
                runner.storage_volumes[("alpha", "pool")].append({"name": "data", "type": "custom", "content_type": "filesystem",
                    "project": "alpha", "config": {}, "location": "none", "used_by": []})
            elif case == "url_default":
                runner.project_links = lambda project, links: [link.split("?")[0] if project == "alpha" and "/volumes/" in link else link for link in links]
            else:
                runner.profile_devices["alpha"]["disk"] = {"type": "disk", "pool": "pool", "source": "data/snap", "path": "/data"}
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                self._network_rows(runner)

    def test_storage_list_detail_type_location_content_and_global_view_agreement(self) -> None:
        for boundary in ("incus_instance_config_show", "incus_instance_config_show_expanded", "incus_storage_volume_show"):
            for field, invalid in (("location", "member"), ("location", ""), ("type", "virtual-machine")):
                runner = self._InventoryRunner()
                runner.detail_overrides[boundary] = {field: invalid}
                with self.subTest(boundary=boundary, field=field, invalid=invalid), self.assertRaises(inventory.InventoryError):
                    inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)
        for field, invalid in (("content_type", "block"), ("location", "")):
            runner = self._InventoryRunner()
            runner.detail_overrides["lxd_storage_volume_show"] = {field: invalid}
            self._assert_main_blocks_without_private_artifact(runner, "VOLUME_METADATA_LIST_MISMATCH")
        for case in ("hidden", "metadata", "users"):
            runner = self._NetworkRunner()
            def drift(project, kind, row):
                if project == "default" and kind == "storage-pools" and "driver" in row:
                    if case == "metadata":
                        row["config"] = {"user.changed": "x"}
                    elif case == "users":
                        row["used_by"] = []
            if case == "hidden":
                hidden = self._NetworkRunner()
                hidden.hidden_pool_projects.add("default")
                self._assert_main_blocks_without_private_artifact(hidden, "POOL_GLOBAL_VIEW_MISMATCH")
                # A project view missing the globally observed pool cannot be repaired by union.
                with patch.object(runner, "pool_row", wraps=runner.pool_row):
                    rows = self._network_rows(runner)
                rows[1]["pools"] = []
                with self.assertRaisesRegex(inventory.InventoryError, "POOL_GLOBAL_VIEW_MISMATCH"):
                    inventory._validate_storage_graph(rows, inventory._canonical_pools(rows))
            else:
                runner.detail_mutation = drift
                with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                    self._network_rows(runner)

    def test_schema_three_independent_storage_admission_and_named_producer_tampering(self) -> None:
        original = self._network_artifact()
        inventory._validate_artifact(original)
        for case in ("schema2", "canonical", "digest", "root_url", "project_root_url", "root_type", "owner", "location", "producer_name", "producer_type", "duplicate_producer", "projection", "admission", "final_order", "version_order", "missing_final", "inactive_query"):
            artifact = copy.deepcopy(original)
            alpha = artifact["incus_projects"][0]
            instance = alpha["instances"][0]
            if case == "schema2":
                artifact["schema_version"] = 2
            elif case == "canonical":
                artifact["incus_pools"] = []
            elif case == "digest":
                artifact["incus_pools"][0]["metadata_digest"] = "f" * 64
            elif case == "root_url":
                for project in artifact["incus_projects"]:
                    project["pools"][0]["used_by"] = [{"kind": "storage-volumes", "name": "pool/container/web", "project": "alpha"}]
                artifact["incus_pools"][0]["used_by"] = alpha["pools"][0]["used_by"]
            elif case == "project_root_url":
                alpha["used_by"] = [ref for ref in alpha["used_by"] if ref["kind"] != "storage-volumes"]
            elif case == "root_type":
                alpha["pools"][0]["volumes"][0]["type"] = "virtual-machine"
            elif case == "owner":
                alpha["pools"][0]["volumes"][0]["owner_project"] = "default"
            elif case == "location":
                instance["storage_location"] = ""
            elif case == "producer_name":
                instance["effective_storage_devices"][0]["device"] = "eth0"
            elif case == "producer_type":
                next(device for device in instance["expanded_devices"] if device["name"] == "root")["type"] = "nic"
            elif case == "duplicate_producer":
                instance["effective_storage_devices"] *= 2
            elif case == "projection":
                instance["api_storage_devices"], instance["effective_storage_devices"] = instance["effective_storage_devices"], instance["api_storage_devices"]
            elif case == "admission":
                artifact["incus_admission"]["final"]["server_clustered"] = True
            elif case == "final_order":
                artifact["command_records"][2], artifact["command_records"][3] = artifact["command_records"][3], artifact["command_records"][2]
            elif case == "version_order":
                artifact["command_records"][0], artifact["command_records"][1] = artifact["command_records"][1], artifact["command_records"][0]
            elif case == "missing_final":
                artifact["command_records"].pop()
            else:
                artifact["command_records"].append({"command_id": "lxd_project_list", "safe_args": [], "exit_status": 0, "stdout_bytes": 0, "stderr_bytes": 0})
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                inventory._validate_artifact(artifact)
        with self.assertRaises(inventory.InventoryError):
            inventory._validate_storage_graph([], original["incus_pools"])

    def test_root_envelope_errors_and_duplicates_fail_real_main_for_each_family(self) -> None:
        class BadEnvelopeRunner(NativeRuntimeInventoryTests._InventoryRunner):
            def __init__(self, duplicate):
                super().__init__()
                self.duplicate = duplicate

            def run(self, argv, **kwargs):
                status, raw, err = super().run(argv, **kwargs)
                if kwargs["command_id"].endswith("server_root_initial"):
                    if self.duplicate:
                        raw = b'{"metadata":{},"metadata":{}}'
                    else:
                        envelope = json.loads(raw)
                        envelope["status_code"] = 500
                        raw = self._json(envelope)
                return status, raw, err
        for incus in (False, True):
            for duplicate in (False, True):
                with self.subTest(incus=incus, duplicate=duplicate):
                    self._assert_main_blocks_without_private_artifact(BadEnvelopeRunner(duplicate),
                        "INVALID_JSON_DUPLICATE_KEY" if duplicate else "API_RESPONSE_INVALID", incus=incus)
        runner = self._InventoryRunner()
        environment = runner.server_row(True)["environment"]
        environment["server_clustered"] = True
        runner.detail_overrides["incus_server_root_final"] = {"environment": environment}
        self._assert_main_blocks_without_private_artifact(runner, "SERVER_ADMISSION_BLOCKED", incus=True)

    def test_storage_instance_list_identity_is_required_before_root_authority(self) -> None:
        for case in ("type", "missing_location", "foreign_location"):
            runner = self._InventoryRunner()
            listed = {"name": "web", "type": "container", "location": "none", "profiles": ["bravo"], "status": "Running"}
            if case == "type":
                listed["type"] = "virtual-machine"
            elif case == "missing_location":
                listed.pop("location")
            else:
                listed["location"] = "member"
            runner.list_rows["instances"] = [listed]
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                inventory._inventory_client(runner, "incus_system", "/run/incus/unix.socket", incus=True, before_query=lambda: None)

    def test_schema_four_inherited_profiles_both_families_false_absent_and_default_last(self) -> None:
        for incus in (False, True):
            for flag in (None, "false"):
                runner = self._InheritedProfileRunner()
                if flag is None:
                    runner.configs["alpha"].pop("features.profiles")
                rows = self._network_rows(runner, incus=incus)
                self.assertEqual(list(runner.configs), ["alpha", "default"])
                self.assertEqual(rows[0]["effective_profile_project"], "default")
                self.assertEqual(rows[0]["profiles"], rows[1]["profiles"])
                profile = rows[0]["profiles"][0]
                self.assertEqual(profile["owner_project"], "default")
                self.assertEqual(profile["used_by"], [{"kind": "instances", "name": "web", "project": "alpha"}])
                self.assertNotIn({"kind": "profiles", "name": "profile", "project": "alpha"}, rows[0]["used_by"])
                pool_users = rows[0]["pools"][0]["used_by"]
                self.assertEqual(sum(ref["kind"] == "profiles" for ref in pool_users), 1)
                self.assertIn({"kind": "profiles", "name": "profile", "project": "default"}, pool_users)
                artifact = self._valid_artifact()
                self._bind_artifact(artifact, rows, incus=incus)
                self.assertEqual(json.loads(inventory._validate_artifact(artifact))["schema_version"], 4)
                self.assertEqual(sum(call[2].endswith("profile_show") for call in runner.calls), 2)

    def test_canonical_profile_users_span_default_and_inheriting_projects(self) -> None:
        runner = self._InheritedProfileRunner()
        runner.instance_projects.add("default")
        runner.expanded_devices["default"] = copy.deepcopy(runner.profile_devices["default"])
        runner.storage_volumes[("default", "pool")] = [{"name": "web", "type": "container", "content_type": "filesystem",
            "project": "default", "config": {}, "location": "none", "used_by": ["/1.0/instances/web"]}]
        runner.network_users["net"].append("/1.0/instances/web")
        rows = self._network_rows(runner)
        self.assertEqual(rows[1]["profiles"][0]["used_by"], [
            {"kind": "instances", "name": "web", "project": "alpha"},
            {"kind": "instances", "name": "web", "project": "default"}])
        self.assertEqual(rows[0]["profiles"], rows[1]["profiles"])

    def test_owned_same_name_profile_stays_distinct_from_inherited_default(self) -> None:
        runner = self._InheritedProfileRunner()
        runner.configs = {"alpha": runner.configs["alpha"],
                          "beta": {"features.profiles": "true", "features.networks": "false"}, "default": {}}
        runner.profile_devices["beta"] = {}
        runner.expanded_devices["beta"] = {}
        runner.local_devices["beta"] = {}
        runner.root_pools["beta"] = "pool"
        runner.networks["beta"] = copy.deepcopy(runner.networks["default"])
        runner.instance_projects.add("beta")
        runner.profile_order["beta"] = ["profile"]
        runner.storage_volumes[("beta", "pool")] = [{"name": "web", "type": "container", "content_type": "filesystem",
            "project": "beta", "config": {}, "location": "none", "used_by": ["/1.0/instances/web?project=beta"]}]
        rows = self._network_rows(runner)
        self.assertEqual([row["project"] for row in rows], ["alpha", "beta", "default"])
        self.assertEqual(rows[1]["profiles"][0]["owner_project"], "beta")
        self.assertEqual(rows[1]["profiles"][0]["used_by"], [{"kind": "instances", "name": "web", "project": "beta"}])
        self.assertEqual(rows[0]["profiles"], rows[2]["profiles"])
        self.assertNotEqual(rows[1]["profiles"], rows[2]["profiles"])

    def test_profile_owner_is_mandatory_actual_effective_owner_at_each_boundary(self) -> None:
        malformed_owners: tuple[object, ...] = (None, False, 0, [], {}, "", "alpha", "foreign")
        for incus in (False, True):
            for boundary in ("list", "detail"):
                for owner in malformed_owners:
                    runner = self._InheritedProfileRunner()
                    if boundary == "list":
                        runner.profile_list_changes["alpha"] = {"project": owner}
                    else:
                        def change(project, kind, row):
                            if project == "alpha" and kind == "profiles":
                                row["project"] = owner
                        runner.detail_mutation = change
                    with self.subTest(incus=incus, boundary=boundary, owner=owner):
                        self._assert_main_blocks_without_private_artifact(runner, "PROFILE_OWNER_PROJECT_MISMATCH", incus=incus)
        row = {"name": "profile", "config": {}, "devices": {}, "used_by": []}
        with self.assertRaisesRegex(inventory.InventoryError, "PROFILE_OWNER_PROJECT_MISMATCH"):
            inventory._validate_profile_show(row, "profile", "default")

    def test_profile_complete_view_metadata_and_users_are_compared_without_union(self) -> None:
        for case in ("missing_inherited", "missing_canonical", "extra_inherited", "duplicate", "config", "description", "devices", "users"):
            runner = self._InheritedProfileRunner()
            if case == "missing_inherited":
                runner.missing_profile_views.add("alpha")
            elif case == "missing_canonical":
                runner.missing_profile_views.add("default")
            elif case == "extra_inherited":
                runner.extra_profile_views.add("alpha")
            elif case == "duplicate":
                runner.profile_names.append("profile")
            elif case == "config":
                runner.profile_view_changes["alpha"] = {"config": {"user.changed": "x"}}
            elif case == "description":
                runner.profile_view_changes["alpha"] = {"description": "different"}
            elif case == "devices":
                runner.profile_view_changes["alpha"] = {"devices": {"root": {"type": "disk", "pool": "pool", "path": "/"}}}
            else:
                runner.profile_view_changes["alpha"] = {"used_by": []}
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                self._network_rows(runner)
        for field, changed in (("config", {"user.changed": "x"}), ("description", "different"), ("devices", {})):
            runner = self._InheritedProfileRunner()
            runner.profile_list_changes["alpha"] = {field: changed}
            with self.subTest(field=field):
                self._assert_main_blocks_without_private_artifact(runner, "PROFILE_METADATA_LIST_MISMATCH")
        # Optional-field absence and an explicit empty value are different observations.
        runner = self._InheritedProfileRunner()
        runner.profile_view_changes = {"alpha": {"description": ""}, "default": {"description": ""}}
        def omit_description(project, kind, row):
            if project == "alpha" and kind == "profiles":
                row.pop("description")
        runner.detail_mutation = omit_description
        with patch.object(inventory, "_profile_digest", return_value="a" * 64):
            self._assert_main_blocks_without_private_artifact(runner, "PROFILE_METADATA_LIST_MISMATCH")
        # Digest identity cannot substitute for exact RAM map observation equality.
        runner = self._InheritedProfileRunner()
        runner.profile_view_changes["alpha"] = {"config": {"user.changed": "x"}}
        with patch.object(inventory, "_profile_digest", return_value="a" * 64):
            self._assert_main_blocks_without_private_artifact(runner, "PROFILE_INHERITED_VIEW_MISMATCH")

    def test_profile_membership_keeps_order_and_rejects_duplicates_at_all_observations(self) -> None:
        runner = self._InheritedProfileRunner()
        runner.profile_names.append("second")
        runner.profile_order["alpha"] = ["second", "profile"]
        rows = self._network_rows(runner)
        self.assertEqual(rows[0]["instances"][0]["profiles"], ["second", "profile"])
        class ProfileOrderRunner(NativeRuntimeInventoryTests._InheritedProfileRunner):
            def __init__(self, boundary, duplicate):
                super().__init__()
                self.profile_names.append("second")
                self.profile_order["alpha"] = ["second", "profile"]
                self.boundary = boundary
                self.duplicate = duplicate

            def run(self, argv, **kwargs):
                status, raw, err = super().run(argv, **kwargs)
                if kwargs["command_id"].endswith(self.boundary) and "alpha" in (kwargs.get("safe_args") or []):
                    envelope = json.loads(raw)
                    row = envelope["metadata"][0] if isinstance(envelope["metadata"], list) else envelope["metadata"]
                    row["profiles"] = ["profile", "profile"] if self.duplicate else ["profile", "second"]
                    raw = self._json(envelope)
                return status, raw, err
        for boundary in ("instance_list", "instance_config_show", "instance_config_show_expanded"):
            for duplicate in (False, True):
                fixture = ProfileOrderRunner(boundary, duplicate)
                with self.subTest(boundary=boundary, duplicate=duplicate):
                    self._assert_main_blocks_without_private_artifact(fixture,
                        "PROFILE_LIST_INVALID" if duplicate else "INSTANCE_PROFILE_LIST_MISMATCH")
        runner = self._InheritedProfileRunner()
        runner.profile_order["alpha"] = ["missing"]
        with self.assertRaisesRegex(inventory.InventoryError, "PROFILE_REFERENCE_UNRESOLVED"):
            self._network_rows(runner)

    def test_profile_owner_and_instance_network_custom_scopes_are_independent(self) -> None:
        runner = self._InheritedProfileRunner()
        runner.configs["alpha"].update({"features.networks": "true", "features.storage.volumes": "true"})
        runner.networks["alpha"] = [runner.network("net", True)]
        runner.storage_pools.append("data")
        runner.profile_devices["default"]["data"] = {"type": "disk", "path": "/data", "pool": "data", "source": "shared"}
        runner.expanded_devices["alpha"]["data"] = dict(runner.profile_devices["default"]["data"])
        runner.storage_volumes[("default", "data")] = [{"name": "shared", "type": "custom", "content_type": "filesystem",
            "project": "default", "config": {}, "location": "none", "used_by": ["/1.0/profiles/profile"]}]
        runner.storage_volumes[("alpha", "data")] = [{"name": "shared", "type": "custom", "content_type": "filesystem",
            "project": "alpha", "config": {}, "location": "none", "used_by": []}]
        def network_users(project, rows):
            for network in rows:
                if network["name"] == "net":
                    network["used_by"] = ["/1.0/instances/web?project=alpha"] if project == "alpha" else ["/1.0/profiles/profile"]
        runner.list_mutation = network_users
        def detail_users(project, kind, row):
            if kind == "networks":
                network_users(project, [row])
        runner.detail_mutation = detail_users
        for incus in (False, True):
            rows = self._network_rows(runner, incus=incus)
            self.assertEqual(rows[0]["profiles"][0]["network_refs"], [{"project": "default", "name": "net"}])
            self.assertEqual(rows[0]["instances"][0]["network_refs"], [{"project": "alpha", "name": "net"}])
            data_default = next(pool for pool in rows[1]["pools"] if pool["name"] == "data")
            data_alpha = next(pool for pool in rows[0]["pools"] if pool["name"] == "data")
            self.assertEqual(data_default["volumes"][0]["used_by"], [{"kind": "profiles", "name": "profile", "project": "default"}])
            self.assertEqual(data_alpha["volumes"][0]["used_by"], [])
            self.assertEqual(rows[0]["instances"][0]["api_storage_devices"], [])
            artifact = self._valid_artifact()
            self._bind_artifact(artifact, rows, incus=incus)
            inventory._validate_artifact(artifact)

    def test_profile_metadata_canaries_stay_in_ram_and_fixed_errors(self) -> None:
        canary = "profile-canary-not-for-evidence"
        runner = self._InheritedProfileRunner()
        change = {"config": {"user.private": canary}, "description": canary}
        runner.profile_view_changes = {"alpha": dict(change), "default": dict(change)}
        runner.profile_devices["default"]["host"] = {"type": "disk", "source": "/private/" + canary}
        raw = self._assert_main_blocks_without_private_artifact(runner, None)
        self.assertNotIn(canary.encode(), raw or b"")
        self.assertNotIn(canary, json.dumps(runner.records))
        runner = self._InheritedProfileRunner()
        runner.profile_view_changes["alpha"] = {"description": canary}
        self._assert_main_blocks_without_private_artifact(runner, "PROFILE_INHERITED_VIEW_MISMATCH")

    def test_schema_four_reader_rejects_owner_scope_view_membership_and_producer_tampering(self) -> None:
        runner = self._InheritedProfileRunner()
        rows = self._network_rows(runner)
        original = self._valid_artifact()
        self._bind_artifact(original, rows, incus=True)
        inventory._validate_artifact(original)
        for case in ("schema3", "scope", "owner", "owner_type", "flag", "canonical_missing", "inherited_extra", "digest", "consumer_missing", "consumer_wrong_project", "order_duplicate", "membership_missing", "producer_scope", "storage_view", "project_owned_link"):
            value = copy.deepcopy(original)
            alpha, default = value["incus_projects"]
            if case == "schema3":
                value["schema_version"] = 3
            elif case == "scope":
                alpha["effective_profile_project"] = "alpha"
            elif case == "owner":
                alpha["profiles"][0]["owner_project"] = "alpha"
            elif case == "owner_type":
                alpha["profiles"][0]["owner_project"] = None
            elif case == "flag":
                alpha["features_profiles"] = "false"
            elif case == "canonical_missing":
                default["profiles"] = []
            elif case == "inherited_extra":
                extra = copy.deepcopy(alpha["profiles"][0])
                extra["name"] = "extra"
                alpha["profiles"].insert(0, extra)
            elif case == "digest":
                alpha["profiles"][0]["metadata_digest"] = "f" * 64
            elif case in {"consumer_missing", "consumer_wrong_project"}:
                for project in (alpha, default):
                    project["profiles"][0]["used_by"] = [] if case == "consumer_missing" else [{"kind": "instances", "name": "web", "project": "default"}]
            elif case == "order_duplicate":
                alpha["instances"][0]["profiles"] *= 2
            elif case == "membership_missing":
                alpha["instances"][0]["profiles"] = ["missing"]
            elif case == "producer_scope":
                alpha["profiles"][0]["network_refs"][0]["project"] = "alpha"
            elif case == "storage_view":
                alpha["profiles"][0]["api_storage_devices"] = []
            else:
                alpha["used_by"].append({"kind": "profiles", "name": "profile", "project": "alpha"})
            with self.subTest(case=case), self.assertRaises(inventory.InventoryError):
                inventory._validate_artifact(value)

    def test_device_entries_are_counted_toward_inventory_entity_cap(self) -> None:
        runner = self._InventoryRunner()
        with patch.object(inventory, "MAX_ENTITIES", 6), self.assertRaisesRegex(inventory.InventoryError, "ENTITY_LIMIT"):
            inventory._inventory_client(runner, "lxd_system", "/var/lib/lxd/unix.socket",
                                        incus=False, before_query=lambda: None)

    def test_runner_timeout_and_aggregate_wall_clock_fail_closed(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 99
        proc.kill = Mock()
        proc.wait.return_value = 0
        ticks = iter((0.0, 0.0, 0.0, inventory.MAX_COMMAND_SECONDS + 1.0,
                      inventory.MAX_COMMAND_SECONDS + 1.0))
        timed = inventory.Runner(popen=Mock(return_value=proc), clock=lambda: next(ticks))
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "killpg"), self.assertRaisesRegex(inventory.InventoryError, "COMMAND_TIMEOUT"):
            timed.run(["/usr/bin/systemctl", "show"], command_id="timeout")
        clock_state = {"now": 0.0}
        bounded = inventory.Runner(popen=Mock(), clock=lambda: clock_state["now"])
        clock_state["now"] = inventory.MAX_WALL_SECONDS + 1.0
        with self.assertRaisesRegex(inventory.InventoryError, "INVENTORY_BUDGET_EXCEEDED"):
            bounded.run(["/usr/bin/systemctl", "show"], command_id="wall")

    def test_aggregate_wall_clock_expiring_during_child_kills_and_fails_closed(self) -> None:
        proc = Mock()
        proc.stdout = Mock()
        proc.stdout.fileno.return_value = 101
        proc.stderr = Mock()
        proc.stderr.fileno.return_value = 102
        proc.pid = 99
        proc.kill = Mock()
        proc.wait.return_value = 0
        clock_now = 0.0
        clock_sequence: list[float] = []
        def advancing_clock() -> float:
            if clock_sequence:
                return clock_sequence.pop(0)
            return clock_now
        runner = inventory.Runner(popen=Mock(return_value=proc), clock=advancing_clock)
        clock_sequence.extend((inventory.MAX_WALL_SECONDS - 1.0,
                               inventory.MAX_WALL_SECONDS - 1.0,
                               inventory.MAX_WALL_SECONDS - 1.0,
                               inventory.MAX_WALL_SECONDS + 1.0))
        with patch.object(inventory.selectors, "DefaultSelector", self._Selector), \
                patch.object(inventory.os, "killpg") as kill_group, \
                self.assertRaisesRegex(inventory.InventoryError, "COMMAND_TIMEOUT"):
            runner.run(["/usr/bin/systemctl", "show"], command_id="aggregate-timeout")
        kill_group.assert_called_once_with(proc.pid, inventory.signal.SIGKILL)
        proc.wait.assert_called()

    def test_serialized_artifact_size_limit_is_enforced(self) -> None:
        with patch.object(inventory, "MAX_ARTIFACT", 1), \
                self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_LIMIT"):
            inventory._validate_artifact(self._valid_artifact())

    def test_capture_failure_does_not_create_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "never-created.json"
            stderr = StringIO()
            with patch.object(inventory, "capture", side_effect=inventory.InventoryError("FIXTURE_FAILURE")), \
                    patch.object(inventory, "_write_private") as write, redirect_stderr(stderr):
                result = inventory.main(["--source-commit", "a" * 40, "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertFalse(output.exists())
            write.assert_not_called()
            self.assertEqual(stderr.getvalue().strip(), "BLOCKED:FIXTURE_FAILURE")

    def test_private_writer_uses_exclusive_owner_only_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = Path("private/evidence/inventory.json")
            target = root / relative
            mountinfo = "29 23 0:26 / / rw,relatime - ext4 /dev/sda rw\n"
            with patch.object(inventory, "ROOT", root), patch.object(inventory, "PRIVATE_REL", relative), \
                    patch.object(Path, "read_text", return_value=mountinfo):
                inventory._write_private(target, b"safe\n")
                self.assertEqual(target.read_bytes(), b"safe\n")
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)
                with self.assertRaisesRegex(inventory.InventoryError, "ARTIFACT_PATH_EXISTS"):
                    inventory._write_private(target, b"replacement\n")


class SnapWrapperIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.row = {"unit": "snap.lxd.daemon.service", "load_state": "loaded", "active_state": "active",
                    "sub_state": "running", "unit_file_state": "enabled", "main_pid": 101}

    def test_fallback_normalizes_only_the_snap_unit_after_helper_success(self) -> None:
        from tools.linux.qualification import native_lxd_snap_provenance as proof
        runner = Mock()
        with patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper", return_value=("lxd_snap", "snap:lxd")) as verify:
            self.assertEqual(inventory._resolve_executable(runner, self.row), ("lxd_snap", "snap:lxd"))
        verify.assert_called_once_with(runner, self.row)

    def test_direct_existing_identity_does_not_need_the_helper(self) -> None:
        from tools.linux.qualification import native_lxd_snap_provenance as proof
        with patch.object(inventory, "_read_executable_path", return_value="/snap/lxd/123/bin/lxd"), \
                patch.object(proof, "prove_snap_wrapper") as verify:
            self.assertEqual(inventory._resolve_executable(Mock(), self.row), ("lxd_snap", "snap:lxd"))
        verify.assert_not_called()

    def test_other_units_and_readlink_failures_do_not_reach_fallback(self) -> None:
        from tools.linux.qualification import native_lxd_snap_provenance as proof
        with patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper") as verify:
            with self.assertRaisesRegex(inventory.InventoryError, "^EXECUTABLE_IDENTITY_BLOCKED$"):
                inventory._resolve_executable(Mock(), {**self.row, "unit": "incus.service"})
        verify.assert_not_called()

        with patch.object(inventory, "_read_executable_path", side_effect=inventory.InventoryError("COMMAND_FAILED")), \
                patch.object(proof, "prove_snap_wrapper") as verify:
            with self.assertRaisesRegex(inventory.InventoryError, "^COMMAND_FAILED$"):
                inventory._resolve_executable(Mock(), self.row)
        verify.assert_not_called()

    def test_missing_helper_dependency_is_a_fixed_inventory_error(self) -> None:
        with patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch("importlib.import_module", side_effect=ModuleNotFoundError("secret-value")):
            with self.assertRaisesRegex(inventory.InventoryError, "^SNAP_WRAPPER_METADATA_INVALID$"):
                inventory._resolve_executable(Mock(), self.row)

    def test_failed_proof_blocks_capture_before_endpoint_client_or_artifact_work(self) -> None:
        from tools.linux.qualification import native_lxd_snap_provenance as proof
        inactive = {"unit": "", "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                    "unit_file_state": "", "main_pid": 0, "listen": ""}
        rows = {unit: ({**self.row} if unit == self.row["unit"] else {**inactive, "unit": unit}) for unit in inventory.UNITS}
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper", side_effect=proof.ProvenanceError("SNAP_WRAPPER_CHILD_ABSENT")), \
                patch.object(inventory, "_endpoint") as endpoint, \
                patch.object(inventory, "_inventory_client") as client, \
                patch.object(inventory, "_write_private") as writer:
            with self.assertRaisesRegex(inventory.InventoryError, "^SNAP_WRAPPER_CHILD_ABSENT$"):
                inventory.capture("a" * 40, runner=Mock())
        endpoint.assert_not_called()
        client.assert_not_called()
        writer.assert_not_called()

    def test_successful_proof_still_requires_existing_socket_binding(self) -> None:
        from tools.linux.qualification import native_lxd_snap_provenance as proof
        inactive = {"unit": "", "load_state": "not-found", "active_state": "inactive", "sub_state": "dead",
                    "unit_file_state": "", "main_pid": 0, "listen": ""}
        rows = {unit: ({**self.row} if unit == self.row["unit"] else {**inactive, "unit": unit}) for unit in inventory.UNITS}
        with patch.object(inventory, "_systemctl_show", side_effect=lambda _runner, unit: rows[unit]), \
                patch.object(inventory, "_read_executable_path", return_value="/usr/bin/dash"), \
                patch.object(proof, "prove_snap_wrapper", return_value=("lxd_snap", "snap:lxd")), \
                patch.object(inventory, "_endpoint", return_value=("", False)), \
                patch.object(inventory, "_inventory_client") as client:
            with self.assertRaisesRegex(inventory.InventoryError, "^ACTIVE_LXD_SOCKET_MISSING$"):
                inventory.capture("a" * 40, runner=Mock())
        client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
