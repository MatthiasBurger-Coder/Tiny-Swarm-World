---
name: workspace-lifecycle-specialist
description: Use for repository workspace lifecycle, isolation, checkout preparation, cleanup, caching, locking, and disk-pressure planning.
---

# Skill: Workspace Lifecycle Specialist

## Description

Guides workspace lifecycle design for repository checkout and analysis preparation before parser or analyzer execution.

## Instructions

1. Verify existing workspace, project storage, repository source, and analysis-session concepts before proposing new names.
2. Keep repository lifecycle explicit: requested workspace, creation, checkout, ready state, failure state, lease ownership, cleanup, and audit trace.
3. Design workspace isolation so untrusted repositories cannot escape server-managed workspace roots.
4. Plan ephemeral workspaces, cleanup strategies, disk pressure handling, concurrent workspace handling, lock management, and lease expiration.
5. Support branch and commit pinning. Prefer exact commit verification after checkout.
6. Treat shallow clone optimization, partial clone, sparse checkout, repository caching, and mirrors as optional policies behind ports.
7. Ensure source root detection is metadata preparation only. Do not execute parsers or analyzers in this phase.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for workspace timeouts, leases, cleanup, retry safety, health checks, partial failures and degraded readiness decisions.

## Expected Inputs

- workspace and project domain models
- repository source and source snapshot models
- planned gRPC request metadata
- filesystem storage boundaries
- security and cleanup requirements

## Expected Outputs

- workspace lifecycle model
- workspace policy and cleanup policy notes
- lock and lease strategy
- checkout-to-source-root preparation plan
- integration-test scenarios for mini repositories and large repositories

## Boundaries

- Filesystem workspace behavior belongs in outbound adapters or infrastructure.
- Domain and application models must not depend on concrete filesystem APIs beyond value objects.
- Do not replace server-side workspaces with plugin-local analysis paths.

## Stop Conditions

Stop if:

- workspace root constraints cannot be verified;
- checkout inputs omit repository, branch, and commit provenance required for deterministic replay;
- cleanup behavior could delete paths outside the intended workspace root;
- source root detection would require parser execution.
