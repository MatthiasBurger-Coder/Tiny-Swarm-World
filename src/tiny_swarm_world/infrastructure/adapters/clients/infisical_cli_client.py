from __future__ import annotations

import json
import os
import shutil
import subprocess

import requests

from tiny_swarm_world.application.ports.clients.port_infisical_cli import (
    InfisicalCliResult,
    PortInfisicalCli,
)


class InfisicalCliClient(PortInfisicalCli):
    def __init__(self, *, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("TSW_INFISICAL_URL") or "http://localhost:8086").rstrip("/")
        self._bootstrap_payload: dict[str, object] = {}
        self._project_ids: dict[str, str] = {}

    def is_available(self) -> bool:
        return shutil.which("infisical") is not None

    def run_bootstrap(self, args: tuple[str, ...]) -> InfisicalCliResult:
        result = _run(args)
        output = result.stdout.strip() or result.stderr.strip()
        if result.return_code == 0 and output:
            try:
                payload = json.loads(output)
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                self._bootstrap_payload = payload
                token = _bootstrap_token(payload)
                if token:
                    os.environ["TSW_INFISICAL_BOOTSTRAP_TOKEN"] = token
        return result

    def ensure_project_environment(self, project: str, environment: str) -> None:
        project_id = self._ensure_project(project)
        self._ensure_environment(project_id, environment)

    def secret_exists(self, key: str, *, project: str, environment: str) -> bool:
        project_id = self._project_ids.get(project) or self._ensure_project(project)
        response = self._request(
            "GET",
            f"/api/v3/secrets/raw?workspaceId={project_id}&environment={environment}&secretPath=%2F",
        )
        if response.status_code >= 400:
            return False
        return key in _secret_keys(response.json())

    def set_secret(self, key: str, value: str, *, project: str, environment: str) -> None:
        project_id = self._project_ids.get(project) or self._ensure_project(project)
        payload = {
            "workspaceId": project_id,
            "environment": environment,
            "secretPath": "/",
            "secretValue": value,
            "type": "shared",
        }
        response = self._request(
            "POST",
            f"/api/v3/secrets/raw/{key}",
            json=payload,
        )
        if response.status_code == 400:
            response = self._request(
                "PATCH",
                f"/api/v3/secrets/raw/{key}",
                json=payload,
            )
        if response.status_code >= 400:
            raise RuntimeError("Infisical managed entry set failed with redacted output.")

    def _ensure_project(self, project: str) -> str:
        if project in self._project_ids:
            return self._project_ids[project]
        existing = self._find_project(project)
        if existing:
            self._project_ids[project] = existing
            return existing
        response = self._request(
            "POST",
            "/api/v1/projects",
            json={
                "projectName": project,
                "slug": project,
                "type": "secret-manager",
                "shouldCreateDefaultEnvs": True,
            },
        )
        if response.status_code >= 400:
            existing = self._find_project(project)
            if existing:
                self._project_ids[project] = existing
                return existing
            raise RuntimeError("Infisical project ensure failed with redacted output.")
        project_id = _project_id(response.json())
        if not project_id:
            raise RuntimeError("Infisical project ensure failed with redacted output.")
        self._project_ids[project] = project_id
        return project_id

    def _find_project(self, project: str) -> str:
        response = self._request("GET", "/api/v1/projects")
        if response.status_code >= 400:
            return ""
        return _project_id_by_name(response.json(), project)

    def _ensure_environment(self, project_id: str, environment: str) -> None:
        response = self._request(
            "POST",
            f"/api/v1/projects/{project_id}/environments",
            json={"name": environment, "slug": environment, "position": 10},
        )
        if response.status_code in {200, 201, 400, 409, 422}:
            return
        raise RuntimeError("Infisical environment ensure failed with redacted output.")

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        return requests.request(
            method,
            f"{self.base_url}{path}",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
            timeout=30,
            **kwargs,
        )

    def _access_token(self) -> str:
        token = (
            os.environ.get("TSW_INFISICAL_TOKEN")
            or os.environ.get("TSW_INFISICAL_BOOTSTRAP_TOKEN")
            or os.environ.get("INFISICAL_TOKEN")
        )
        if token:
            return token
        identity = self._bootstrap_payload.get("identity")
        if not isinstance(identity, dict):
            raise RuntimeError("Infisical sync session is unavailable.")
        credentials = identity.get("credentials")
        if not isinstance(credentials, dict):
            raise RuntimeError("Infisical sync session is unavailable.")
        token_value = credentials.get("token")
        if not isinstance(token_value, str) or not token_value.strip():
            raise RuntimeError("Infisical sync session is unavailable.")
        return token_value


def _project_id(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    project = payload.get("project")
    if isinstance(project, dict):
        value = project.get("id")
        return value if isinstance(value, str) else ""
    value = payload.get("id")
    return value if isinstance(value, str) else ""


def _bootstrap_token(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    identity = payload.get("identity")
    if not isinstance(identity, dict):
        return ""
    credentials = identity.get("credentials")
    if not isinstance(credentials, dict):
        return ""
    token = credentials.get("token")
    return token if isinstance(token, str) else ""


def _project_id_by_name(payload: object, project: str) -> str:
    candidates: list[object] = []
    if isinstance(payload, list):
        candidates = list(payload)
    elif isinstance(payload, dict):
        for key in ("projects", "workspaces"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates = value
                break
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        names = {str(candidate.get("name", "")), str(candidate.get("projectName", "")), str(candidate.get("slug", ""))}
        if project in names:
            value = candidate.get("id")
            return value if isinstance(value, str) else ""
    return ""


def _secret_keys(payload: object) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    secrets = payload.get("secrets")
    if not isinstance(secrets, list):
        return set()
    keys: set[str] = set()
    for item in secrets:
        if not isinstance(item, dict):
            continue
        key = item.get("secretKey") or item.get("key")
        if isinstance(key, str):
            keys.add(key)
    return keys


def _run(args: tuple[str, ...]) -> InfisicalCliResult:
    result = subprocess.run(
        args,
        capture_output=True,
        check=False,
        text=True,
        timeout=300,
    )
    return InfisicalCliResult(
        return_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
