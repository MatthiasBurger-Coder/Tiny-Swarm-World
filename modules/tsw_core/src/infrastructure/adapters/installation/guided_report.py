"""Report fresh access observations for the committed native installation."""

from collections.abc import Mapping
from datetime import UTC, datetime
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from urllib.parse import urlsplit

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestSnapshot
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.application.ports.repositories.port_routing_evidence_repository import RoutingEvidenceRoute
from tiny_swarm_world.application.services.deployment.write_effective_access_model_evidence import (
    build_effective_access_model_evidence,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile, service_stack_contracts_for_profile
from tiny_swarm_world.domain.ingress.desired_state import DirectServiceEndpoint
from tiny_swarm_world.domain.lifecycle.models import InstallationManifest
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import (
    ComposeFileRepositoryYaml,
)
from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service
from tiny_swarm_world.infrastructure.project_paths import default_project_paths


def report_service_access(profile: str, environment: Mapping[str, str]) -> bool:
    try:
        paths = default_project_paths()
        snapshot: ManifestSnapshot = build_installation_lifecycle_service(paths.repository_root).manifests.load()
        manifest = _native_selection(snapshot, profile)
        repository = ComposeFileRepositoryYaml(
            project_paths=paths,
            environment=environment,
            service_profile=ServiceStackProfile(profile),
            resolved_services=manifest.resolved_services,
            service_exposure=manifest.effective_exposure(),
            write_logs=False,
        )
        access_model = repository.get_effective_access_model()
        evidence = build_effective_access_model_evidence(
            access_model,
            service_profile=profile,
            generated_at=datetime.now(UTC).isoformat(),
        )
        contracts = service_stack_contracts_for_profile(
            ServiceStackProfile(profile), manifest.resolved_services, service_exposure=manifest.effective_exposure(),
        )
    except (OSError, ValueError, OperationError):
        print("Service access: unverified. The committed selection or access model is unavailable.", flush=True)
        return False

    print("Service access checks from this host (system TLS trust, HTTP responses only).", flush=True)
    endpoints: tuple[RoutingEvidenceRoute | DirectServiceEndpoint, ...] = (
        *evidence.routes, *access_model.direct_endpoints,
    )
    published = {endpoint.service_name for endpoint in endpoints}
    published.update(contract.stack_name for contract in contracts
                     if any(endpoint.name in published for endpoint in contract.endpoints))
    for service in sorted(set(manifest.resolved_services) - published):
        print(f"{service}: no published URL in the access model; health unverified.", flush=True)
    for endpoint in sorted(endpoints, key=lambda item: (item.service_name, item.service_access_url)):
        access_url, health_url = endpoint.service_access_url, endpoint.health_check_url
        if not (access_url.isprintable() and health_url.isprintable()):
            print(f"{endpoint.service_name}: invalid published URL; health unverified.", flush=True)
            continue
        access_status = _http_status(access_url)
        health_status = access_status if health_url == access_url else _http_status(health_url)
        health = "passed" if _successful(health_status) else "unverified"
        observed = datetime.now(UTC).isoformat(timespec="seconds")
        print(f"{endpoint.service_name}: health probe {health} ({_observation(health_status)}); "
              f"{_access_label(access_status)} {access_url} ({_observation(access_status)}); {observed}.",
              flush=True)
    return True


def _native_selection(snapshot: ManifestSnapshot, profile: str) -> InstallationManifest:
    manifest = snapshot.manifest
    if snapshot.diagnostics or manifest is None or manifest.host != "native-linux" or manifest.service_preset != profile:
        raise LifecycleStateError("No matching committed native selection.")
    return manifest


def _http_status(url: str) -> int | None:
    """Read response headers only, without proxy settings, redirects or credentials."""
    target = urlsplit(url)
    if target.hostname is None:
        return None
    connection_type = HTTPSConnection if target.scheme == "https" else HTTPConnection
    connection = connection_type(target.hostname, target.port, timeout=3)
    try:
        connection.request("GET", target.path or "/")
        with connection.getresponse() as response:
            return response.status
    except (OSError, HTTPException, ValueError):
        return None
    finally:
        connection.close()


def _access_label(status: int | None) -> str:
    if _successful(status):
        return "verified URL"
    if status in (401, 403):
        return "authentication or authorization required at"
    if status is not None and 300 <= status < 400:
        return "redirect observed at"
    return "unverified URL"


def _successful(status: int | None) -> bool:
    return status is not None and 200 <= status < 300


def _observation(status: int | None) -> str:
    return f"HTTP {status}" if status is not None else "no HTTP response"
