"""Thin operator boundary for the separately consented Incus capability."""
from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from tiny_swarm_world.application.ports.incus_preparation import IncusPreparationFailure
from tiny_swarm_world.infrastructure.composition_native_preparation import build_incus_preparation_service


async def prepare(*, read_only: bool, service_profile: str) -> int:
    service = build_incus_preparation_service(service_profile=service_profile)
    earlier_changes = False
    # At most daemon, access and resource stages. Membership changes stop for login.
    for _ in range(3):
        plan = await service.plan()
        for blocker in plan.blockers:
            print(f"BLOCKED: {blocker}")
        if plan.blockers:
            print("Next: ./prepare_linux.sh --dry-run after resolving the reported blocker.")
            return 4 if earlier_changes else 2
        if plan.restart_required:
            print("RESTART_REQUIRED: Log out and log in to activate incus-admin access; then ./prepare_linux.sh. No install handoff.")
            return 3
        if plan.verified:
            print("READY: Current-user Incus version/info and declared storage/network/profiles verified. Services are not verified.")
            print("Next: ./install.sh --preflight (aggregate/kernel/WSL handoff remains separately governed).")
            return 0
        for action in plan.actions:
            print(f"Incus plan: {action.id}; properties={action.payload or action.name}; privilege={action.privilege}; timeout={action.timeout_seconds:g}s; retries=0; restart={action.restart}.")
        print("Preserve existing daemon configuration, pools, bridges, profiles and unrelated instances.")
        if read_only:
            print("BLOCKED: Incus preparation actions are pending; no host/configuration/state/evidence changes. Next: ./prepare_linux.sh")
            return 2
        try:
            approved = input("Apply exactly this Incus stage? Type 'yes' to continue: ") == "yes"
        except EOFError:
            approved = False
        result = await service.apply(plan, approved=approved)
        print(f"{result.status}: {result.message}")
        if result.evidence_path:
            print(f"Incus evidence: {result.evidence_path}")
        earlier_changes = earlier_changes or bool(result.completed)
        if result.stage_complete:
            continue
        if result.status in {"READY", "RESTART_REQUIRED", "PARTIAL", "FAILED"}:
            if result.status == "READY":
                print("READY: Current-user Incus version/info and declared resources verified. Services are not verified.")
                print("Next: ./install.sh --preflight (aggregate/kernel/WSL handoff remains separately governed).")
            return result.exit_code
        if not result.completed:
            print("Next: ./prepare_linux.sh --dry-run")
            return 4 if earlier_changes else result.exit_code
    print("BLOCKED: Stage budget exhausted. Next: ./prepare_linux.sh --dry-run")
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare only the Incus capability through the qualified Linux preparation owner.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--service-profile", choices=("default", "service-access"), default="service-access")
    args = parser.parse_args(argv)
    try:
        return asyncio.run(prepare(read_only=args.preflight or args.dry_run, service_profile=args.service_profile))
    except KeyboardInterrupt:
        print("Incus preparation interrupted; effects may be partial. Next: ./prepare_linux.sh --dry-run")
        return 130
    except IncusPreparationFailure as error:
        print(f"BLOCKED: {error.code} Next: ./prepare_linux.sh --dry-run")
        return error.exit_code or 2
    except (OSError, RuntimeError, ValueError):
        print("BLOCKED: Incus preparation inventory/evidence failed; inspect the declared provider, host and private state directory. Next: ./prepare_linux.sh --dry-run")
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
