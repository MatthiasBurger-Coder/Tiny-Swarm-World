---
name: swarm-volume-network-governance
description: Use for Docker Swarm volume and network governance in Tiny Swarm World.
---

# Swarm Volume Network Governance

## Purpose

Keep Docker Swarm volumes, overlays, published ports and service networks
explicit, bounded and safe to review.

## Responsibilities

- Preserve service stack boundaries for networks and volumes.
- Avoid host-specific data paths, IPs and secrets.
- Ensure network and volume changes are documented and testable.

## Inputs

- Compose files, stack docs, network configuration and workflow scope.
- Root governance files and affected services.
- Change request for storage or network topology.

## Outputs

- Governance decision, risk notes and verification plan.
- STOP report for cross-stack coupling or unsafe host assumptions.

## Boundaries

- Do not run Docker network or volume mutation commands by default.
- Do not couple services through undocumented shared volumes.

## STOP conditions

- Data ownership or network ownership is ambiguous.
- Verification would mutate Docker resources.
- A proposed shared volume crosses service boundaries unsafely.

## Collaboration with other skills

- Pair with `network-topology-design`.
- Pair with `data-ownership-persistence-steward` when persistence ownership is
  affected.
- Pair with `swarm-stack-deployment`.

## Quality expectations

- Run `git diff --check` and configuration-focused tests when available.
- Report skipped live verification explicitly.
