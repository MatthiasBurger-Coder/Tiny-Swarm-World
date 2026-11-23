"""Read-only proof for ports of an interrupted local Incus installation."""

from __future__ import annotations

from pathlib import Path

from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
from tiny_swarm_world.application.services.installation_profile import (
    InstallationProfileService,
    observe_checkpoint,
    require_running,
)
from tiny_swarm_world.application.services.platform.preflight_service import RecoveryPortProof
from tiny_swarm_world.application.services.profile_setup import routes_from_setup_manifest
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import (
    ProfileLifecycleCheckpoint,
    installation_manifest_sha256,
)
from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan
from tiny_swarm_world.domain.preflight.setup_manifest import default_setup_manifest
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.host.host_environment_detector import HostEnvironmentDetector
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import JsonProfileChangeJournal
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import (
    IncusProfileCapabilityRepository,
)
from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service
from tiny_swarm_world.infrastructure.composition_profile import selected_listen_address


def _running_manager_was_recorded(checkpoint: ProfileLifecycleCheckpoint) -> bool:
    if checkpoint.settled or checkpoint.instance_uuid is None:
        return False
    stage = checkpoint.previous_stage if checkpoint.stage == "recoverable" else checkpoint.stage
    if stage == "routes-verified":
        return checkpoint.pending_action == "instance-start"
    if stage == "instance-started":
        return checkpoint.pending_action is None
    return stage == "completed" and checkpoint.pending_action in {None, "worker-init", "worker-start"}


def _matches_creation_baseline(checkpoint: ProfileLifecycleCheckpoint, snapshot: ManifestSnapshot) -> bool:
    intent = checkpoint.intent
    initial = intent.initial_manifest
    return (
        snapshot.manifest is None
        and snapshot.token == intent.profile.manifest_token
        and not any(note.startswith("interrupted_write") for note in snapshot.diagnostics)
        and initial is not None
        and initial.host == "native-linux"
        and initial.product.revision == intent.profile.controller_revision
        and intent.profile.operation_kind == "setup"
    )


def _matches_selection(checkpoint: ProfileLifecycleCheckpoint, plan: SelectionPlan) -> bool:
    intent = checkpoint.intent
    desired = intent.profile
    binding = desired.profile
    if (
        binding is None
        or plan.removals
        or plan.manifest_token != desired.manifest_token
        or plan.requested_services != desired.requested_services
        or plan.resolved_services != desired.resolved_services
        or plan.service_exposure != desired.service_exposure
        or plan.stack_owners != intent.planned_stack_owners
    ):
        return False
    setup_manifest = default_setup_manifest(
        service_profile=plan.service_preset,
        resolved_services=plan.resolved_services,
        service_exposure=plan.service_exposure,
    )
    listen_address = selected_listen_address()
    return (
        routes_from_setup_manifest(setup_manifest, intent) == binding.routes
        and all(route.listen_address == listen_address for route in binding.routes)
    )


def pending_creation_applies(root: Path) -> bool:
    """Use reservation proof before deployment; preserve verified completion admission."""
    try:
        checkpoint = JsonProfileLifecycleJournal(root).load()
        if checkpoint is None or checkpoint.settled:
            return False
        return not _has_original_completion_manifest(root, checkpoint)
    except (OSError, RuntimeError, ValueError):
        return True


def _has_original_completion_manifest(root: Path, checkpoint: ProfileLifecycleCheckpoint) -> bool:
    expected = checkpoint.installation_manifest_sha256
    if checkpoint.stage != "completed" or expected is None:
        return False
    manifest = build_installation_lifecycle_service(root).manifests.load().manifest
    return manifest is not None and installation_manifest_sha256(manifest) == expected

async def observe_recovery_ports(
    root: Path, service_profile: ServiceStackProfile | str,
) -> RecoveryPortProof | None:
    """Prove each admitted local listener against a stable pending creation."""
    try:
        if HostEnvironmentDetector().detect().environment is not HostEnvironmentKind.NATIVE_LINUX:
            return None
        return await _observe_pending_creation(root, ServiceStackProfile(service_profile))
    except (OSError, RuntimeError, ValueError):
        # Unknown ownership leaves ordinary occupied-port checks in control.
        return None


async def _observe_pending_creation(
    root: Path, service_profile: ServiceStackProfile,
) -> RecoveryPortProof | None:
    journal = JsonProfileLifecycleJournal(root)
    changes = JsonProfileChangeJournal(root)
    checkpoint = journal.load()
    if checkpoint is None or not _running_manager_was_recorded(checkpoint) or changes.load() is not None:
        return None
    lifecycle = build_installation_lifecycle_service(root)
    snapshot = lifecycle.manifests.load()
    if not _matches_creation_baseline(checkpoint, snapshot):
        return None
    plan = ServiceSelectionService(lifecycle.manifests, lifecycle.catalog).preview(preset=service_profile.value)
    if not _matches_selection(checkpoint, plan):
        return None
    intent = checkpoint.intent
    runtime = IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner()).for_observation(intent)
    capabilities = IncusProfileCapabilityRepository(root)
    matrix = capabilities.load()
    if await runtime.clean_source_revision(root) != intent.profile.controller_revision:
        return None
    service = InstallationProfileService(capabilities, runtime, journal, lifecycle.manifests, lifecycle.operation_lock)
    before = await observe_checkpoint(service, checkpoint, matrix)
    require_running(before)
    after = await observe_checkpoint(service, checkpoint, matrix)
    require_running(after)
    if not (
        before == after
        and await runtime.clean_source_revision(root) == intent.profile.controller_revision
        and lifecycle.manifests.load() == snapshot
        and journal.load() == checkpoint
        and changes.load() is None
        and _matches_selection(checkpoint, plan)
    ):
        return None
    binding = intent.profile.profile
    assert binding is not None
    return RecoveryPortProof(
        ports=frozenset(route.listen_port for route in binding.routes),
        observation_sha256=after.observation_sha256,
    )
