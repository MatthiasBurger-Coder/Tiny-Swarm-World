"""Thin exact-plan consent boundary; services and login remain separate."""
from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from tiny_swarm_world.application.ports.network_preparation import NetworkPreparationFailure
from tiny_swarm_world.infrastructure.composition_native_preparation import build_network_preparation_service, request_network_consent


async def prepare(*, read_only: bool, service_profile: str) -> int:
    service = build_network_preparation_service(service_profile=service_profile)
    plan = await service.plan()
    for blocker in plan.blockers:
        print(f"BLOCKED: {blocker}")
    if plan.blockers:
        return 2
    for action in plan.actions:
        print(f"Network plan: {action.id}; {action.description}; timeout={action.timeout_seconds:g}s; retries=0.")
    if plan.verified:
        print("READY: Linux network prerequisites and applicable Windows bridge registration/configuration/agent observed. Endpoints and login UNVERIFIED; services_verified=false.")
        return 0
    if read_only:
        print("BLOCKED: Network actions pending; no host/configuration/state/evidence changes. Next: ./prepare_linux.sh")
        return 2
    approved = await request_network_consent()
    result = await service.apply(plan, approved=approved)
    print(f"{result.status}: {result.message} Endpoints and login UNVERIFIED; services_verified=false.")
    if result.evidence_path:
        print(f"Network evidence: {result.evidence_path}")
    return result.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare scoped host network prerequisites without deployment.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--service-profile", choices=("default", "service-access"), default="service-access")
    args = parser.parse_args(argv)
    try:
        return asyncio.run(prepare(read_only=args.preflight or args.dry_run, service_profile=args.service_profile))
    except KeyboardInterrupt:
        print("PARTIAL: Network preparation interrupted; inspect ./prepare_linux.sh --dry-run.")
        return 130
    except NetworkPreparationFailure as error:
        print(f"BLOCKED: {error.code}")
        return error.exit_code or 2
    except (OSError, RuntimeError, ValueError, TimeoutError):
        print("BLOCKED: Network inventory/evidence unavailable; inspect ./prepare_linux.sh --dry-run.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
