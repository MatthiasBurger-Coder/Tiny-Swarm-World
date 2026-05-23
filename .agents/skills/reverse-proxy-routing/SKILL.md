---
name: reverse-proxy-routing
description: Use for NGINX or reverse proxy routing guidance in Tiny Swarm World.
---

# Reverse Proxy Routing

## Purpose

Guide reverse proxy route, port and service-name decisions for local Swarm
services.

## Responsibilities

- Keep routing rules deterministic and service-specific.
- Preserve network topology, ports and DNS assumptions explicitly.
- Prevent route changes from crossing service boundaries without review.

## Inputs

- NGINX or proxy config, compose assets, service docs and workflow scope.
- Network topology and service endpoint requirements.
- Root governance files.

## Outputs

- Routing guidance, conflict notes and verification plan.
- STOP report for ambiguous routing ownership.

## Boundaries

- Do not run proxy reload, compose or Swarm commands unless explicitly
  requested.
- Do not embed host-specific addresses or credentials.

## STOP conditions

- Route ownership or service endpoint is unclear.
- Verification would mutate running services.
- Routing conflicts with network topology decisions.

## Collaboration with other skills

- Pair with `network-topology-design`.
- Pair with `swagger-ui-bootstrap` and service bootstrap skills.
- Pair with `swarm-volume-network-governance`.

## Quality expectations

- Run `git diff --check` and config-focused tests where available.
- Report skipped live route verification.
