"""Bind guided consent to observed host and lifecycle inputs in memory."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING

from tiny_swarm_world.application.ports.installation import CommittedGuidedInstallation, GuidedObservation, GuidedPlanRefused, InstallerOptions
from tiny_swarm_world.infrastructure.adapters.guided_setup import EXPECTED_ENV, GUIDED_PLAN_REFUSED, PLAN_ENV

if TYPE_CHECKING:
    from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
    from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileLifecycleCheckpoint


def committed_installation(snapshot: ManifestSnapshot, creation: ProfileLifecycleCheckpoint | None) -> CommittedGuidedInstallation | None:
    from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
    from tiny_swarm_world.application.services.profile_completion import require_commit_candidate
    from tiny_swarm_world.domain.lifecycle.profile_lifecycle import installation_manifest_sha256

    manifest = snapshot.manifest
    if (creation is None or not creation.installation_committed or manifest is None
            or manifest.host != "native-linux" or snapshot.diagnostics
            or creation.intent.profile.operation_kind != "setup"):
        return None
    digest = installation_manifest_sha256(manifest)
    if creation.installation_manifest_sha256 != digest:
        return None
    try:
        require_commit_candidate(creation, manifest)
    except LifecycleStateError:
        return None
    return CommittedGuidedInstallation(manifest.service_preset, digest)


def guided_observation(nonce: str, effective: Mapping[str, str], cwd: Path, output: str) -> GuidedObservation:
    from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import JsonProfileChangeJournal
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
    from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service

    try:
        checks = json.loads(output)["checks"]
        ports = [(check["check_id"], check["message"], check["evidence"])
                 for check in checks if check["category"] == "PORT"]
        lifecycle = build_installation_lifecycle_service(cwd)
        snapshot = lifecycle.manifests.load()
        creation = JsonProfileLifecycleJournal(cwd).load()
        change = JsonProfileChangeJournal(cwd).load()
        committed = committed_installation(snapshot, creation) if change is None else None
        if committed is not None and creation is not None:
            binding = creation.intent.profile.profile
            route_ports = {str(route.listen_port) for route in binding.routes} if binding else set()
            owned = [evidence.get("source") == "installation_owned_proxy" for _, _, evidence in ports
                     if evidence["port"] in route_ports]
            if not owned or not all(owned) or any(
                evidence.get("source") == "installation_owned_proxy" and evidence["port"] not in route_ports
                for _, _, evidence in ports
            ):
                committed = None
    except (KeyError, TypeError, ValueError, OSError, LifecycleStateError):
        raise GuidedPlanRefused("Guided inventory or lifecycle evidence could not be observed safely.") from None
    scoped_recovery = ((creation is not None and not creation.installation_committed)
                       or (change is not None and not change.settled))
    # Keep the credential-bearing snapshot in memory and bind only stable observations.
    state = (
        {key: value for key, value in effective.items() if key not in {"_", "SHLVL"}},
        ports,
        snapshot.token,
        creation.model_dump(mode="json") if creation else None,
        change.model_dump(mode="json") if change else None,
    )
    payload = json.dumps(state, sort_keys=True).encode()
    fingerprint = hmac.new(bytes.fromhex(nonce), payload, hashlib.sha256).hexdigest()
    return fingerprint, committed if committed is not None else scoped_recovery


def verified_guided_observation(
    options: InstallerOptions, nonce: str, effective: Mapping[str, str], cwd: Path, output: str,
) -> GuidedObservation:
    observation = guided_observation(nonce, effective, cwd, output)
    committed = observation[1]
    if (options.guided_resume and options.dry_run and isinstance(committed, CommittedGuidedInstallation)
            and options.service_profile == committed.service_profile):
        import asyncio

        from tiny_swarm_world.application.ports.operation_result import OperationError
        from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_completion import verify_guided_completion

        try:
            asyncio.run(verify_guided_completion(cwd, committed, effective["TSW_PORTAINER_ADMIN_PASSWORD"]))
        except (KeyError, OSError, RuntimeError, ValueError, OperationError):
            raise GuidedPlanRefused("Committed installation could not be verified; preserve the recovery checkpoint.") from None
    return observation


def parse_guided_binding(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    args.guided_plan_nonce = None
    args.expected_guided_plan = None
    if not args.guided_plan:
        if args.guided_resume:
            parser.error("Guided recovery requires an observed plan.")
        return
    args.guided_plan_nonce = os.environ.get(PLAN_ENV, "")
    args.expected_guided_plan = os.environ.get(EXPECTED_ENV) or None
    bindings = (args.guided_plan_nonce, args.expected_guided_plan)
    if any(value is not None and not re.fullmatch(r"[0-9a-f]{64}", value) for value in bindings):
        parser.error("Invalid guided plan binding.")
    preview = args.dry_run and args.expected_guided_plan is None
    apply = args.guided_report and args.expected_guided_plan is not None
    if args.confirm_reset or args.non_interactive_live_approval or args.headless or not (preview or apply):
        parser.error("Guided plan binding requires a dry-run or interactive reconciliation.")


def without_binding(environment: Mapping[str, str]) -> dict[str, str]:
    return {key: value for key, value in environment.items() if key not in {PLAN_ENV, EXPECTED_ENV}}


def require_interactive_apply(options: InstallerOptions, *, interactive: bool) -> None:
    if options.expected_guided_plan is not None and (options.headless or not interactive):
        raise GuidedPlanRefused("Use interactive installer approval for guided setup.")


def installer_exit(code: int, *, guided: bool) -> int:
    # Reserve the code for a known pre-mutation refusal from this adapter.
    return 1 if guided and code == GUIDED_PLAN_REFUSED else code
