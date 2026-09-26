"""Stable error types and diagnostics for LXC image publication."""

from __future__ import annotations

import subprocess

from tiny_swarm_world.application.ports.clients.port_container_image_publisher import (
    ImagePublisherOperationRejected as ImagePublisherOperationRejected,
    PublicImagePullRejected as PublicImagePullRejected,
)


REGISTRY_RATE_LIMITED_OPERATOR_ACTION = (
    "Configure Docker Hub authentication, an approved registry mirror, "
    "or a provider-managed image cache."
)





def docker_hub_rate_limited(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stdout}\n{result.stderr}".lower()
    return "pull rate limit" in output or "too many requests" in output


def image_operation_failure_diagnostic(
    operation: str,
    result: subprocess.CompletedProcess[str],
) -> str:
    output = f"{result.stdout}\n{result.stderr}".lower()
    if docker_hub_rate_limited(result):
        return "registry_rate_limited"
    if "connection refused" in output or "no route to host" in output:
        if operation in {"registry_login", "push_image"}:
            return "registry_unreachable"
        return "network_unreachable"
    if "unauthorized" in output or "authentication required" in output:
        return "registry_authentication_failed"
    if "no space left on device" in output:
        return "manager_storage_exhausted"
    if operation == "build_image":
        return "image_build_failed"
    if operation == "push_image":
        return "registry_push_failed"
    if operation == "registry_login":
        return "registry_login_failed"
    return "manager_image_operation_failed"


def image_operation_operator_action(
    operation: str,
    result: subprocess.CompletedProcess[str],
) -> str:
    diagnostic = image_operation_failure_diagnostic(operation, result)
    if diagnostic == "registry_rate_limited":
        return REGISTRY_RATE_LIMITED_OPERATOR_ACTION
    if diagnostic == "registry_unreachable":
        return (
            "Verify that the Nexus Docker hosted registry is reachable from the "
            "manager node at 127.0.0.1:13500."
        )
    if diagnostic == "registry_authentication_failed":
        return "Verify TSW_NEXUS_ADMIN_PASSWORD and Nexus Docker hosted repository access."
    if diagnostic == "manager_storage_exhausted":
        return "Free storage on the manager node before rerunning artifacts prepare."
    if operation == "build_image":
        return (
            "Inspect the manager node Docker build prerequisites and the transferred "
            "image context."
        )
    if operation == "push_image":
        return (
            "Verify the local registry service, repository port, and manager-node "
            "registry trust."
        )
    return "Inspect the manager node Docker daemon and rerun artifacts prepare."
