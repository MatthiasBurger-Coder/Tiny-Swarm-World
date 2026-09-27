"""Compose CLI-selected application workflows without putting execution in the CLI."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tiny_swarm_world.application.services.cli_dispatch import (
    ClassicUpdateActionRequest,
    run_artifact_action,
    run_classic_update_action,
    run_deployment_action,
    run_platform_action,
    require_setup_run,
)
from tiny_swarm_world.application.services.platform.workflow.types import PlatformWorkflowKind
from tiny_swarm_world.domain.preflight import LiveConsent
from tiny_swarm_world.domain.update import ClassicUpdatePlan

from .composition_models import ApplicationServices, ArtifactServices, DeploymentServices


async def execute_cli_workflow(
    *,
    namespace: str,
    action: str,
    platform_kind: PlatformWorkflowKind | None,
    confirmation: str | None,
    live_consent: LiveConsent | None,
    service_profile: object,
    node_provider_request: object,
    allow_wsl_windows_filesystem: bool,
    update_plan: ClassicUpdatePlan | None,
    update_preview: bool,
    update_recover: bool,
    update_stack_name: str | None,
    update_service_name: str | None,
    build_classic_update_workflow: Callable[..., Any],
    build_application_services: Callable[..., ApplicationServices],
    build_artifact_services: Callable[..., ArtifactServices],
    build_deployment_services: Callable[..., DeploymentServices],
    run_setup_with_terminal_status: Callable[..., Any],
) -> Any:
    if platform_kind is PlatformWorkflowKind.UPDATE:
        workflow = build_classic_update_workflow(
            service_profile=service_profile,
            node_provider_request=node_provider_request,
        )
        return await run_classic_update_action(
            workflow,
            ClassicUpdateActionRequest(
                update_plan,
                update_preview,
                update_recover,
                update_stack_name,
                update_service_name,
                live_consent,
            ),
        )
    if platform_kind is not None:
        services = build_application_services(
            live_consent=live_consent,
            service_profile=service_profile,
            node_provider_request=node_provider_request,
            allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
        )
        return await run_platform_workflow(services, platform_kind, confirmation)
    if namespace == "artifacts":
        artifact_services = build_artifact_services(node_provider_request=node_provider_request)
        return await run_artifact_workflow(artifact_services, action)
    if namespace == "deployment":
        deployment_services = build_deployment_services(
            service_profile=service_profile,
            node_provider_request=node_provider_request,
        )
        return await run_deployment_workflow(deployment_services, action)
    if namespace == "setup":
        accepted_consent = require_setup_run(action, live_consent)
        return await run_setup_with_terminal_status(
            accepted_consent,
            action,
            service_profile=service_profile,
            node_provider_request=node_provider_request,
            allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
        )
    raise ValueError(f"Unsupported workflow: {namespace} {action}")


async def run_platform_workflow(
    services: ApplicationServices,
    kind: PlatformWorkflowKind,
    confirmation: str | None,
) -> Any:
    return await run_platform_action(services.platform.lifecycle, kind, confirmation)


async def run_artifact_workflow(services: ArtifactServices, action: str) -> Any:
    return await run_artifact_action(
        action, services.workflows.prepare, services.workflows.verify
    )


async def run_deployment_workflow(services: DeploymentServices, action: str) -> Any:
    return await run_deployment_action(
        action,
        services.workflows.bootstrap,
        services.workflows.apply,
        services.workflows.verify,
    )
