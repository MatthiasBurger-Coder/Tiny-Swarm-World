# Requirement Clarification Gate

## Original Request

```text
workflow create with subagents
```

## Interpreted Intent

Create or regenerate the active Tiny Swarm World workflow from the supplied
Linux/WSL-aware swarm setup draft, with subagent review.

## Change Type

```text
fix / architecture hardening / setup migration / installation validation
```

## Affected Process Strand

```text
workflow authoring, setup preflight, platform setup, Multipass readiness,
network planning, evidence, documentation, quality validation
```

## Affected Architecture Area

```text
Platform boundary, setup orchestration, preflight ports/domain/adapters,
network planning, command diagnostics, console/status output, documentation,
arc42 governance
```

## Explicit Requirements

- Detect Native Linux, WSL2, WSL1 unsupported, unknown unsupported, and
  sandbox unverified environments.
- Block unsupported environments before live mutation.
- Migrate useful `infra/swarm` knowledge behind typed Python contracts.
- Keep `infra/swarm` as legacy evidence only.
- Fail preflight before `platform init` when Multipass is not usable.
- Keep normal quality gates static or mocked.
- Validate sandbox and real WSL2 console separately.

## Implicit Requirements

- Reconcile with existing preflight, setup, and safe-evidence code.
- Preserve hexagonal architecture and current architecture tests.
- Avoid browser React scope.
- Avoid raw host-output persistence.
- Keep automatic host repair out of scope unless separately approved.

## Assumptions

- The supplied draft replaces the older active workflow.
- The requested branch remains active.
- Real WSL2 validation is operator-provided evidence if needed.
- `netsh` remains documentation-only/operator-confirmed guidance.
- Full installation success and preflight-blocked host prerequisite outcomes
  are reported separately.

## Non-Goals

- No Java, Maven, Spring Boot, browser React, npm, Kubernetes-first migration,
  or direct `infra/swarm` execution.
- No live infrastructure commands during normal checks.
- No committed secrets, host IPs, usernames, local paths, raw output, or
  environment payloads.

## Risks

- The source draft can overstate missing behavior because current code already
  contains partial Multipass readiness checks.
- WSL2 behavior can be overclaimed if sandbox evidence is treated as live WSL2
  evidence.
- Evidence redaction can regress if diagnostics add raw command fields.
- Architecture tests can fail if new application service directories are added
  without governance updates.

## Open Questions

- Who runs and approves real WSL2 validation and cleanup?
- Does a later ADR authorize automatic host preparation, or does it remain
  remediation guidance only?

## Blocking Questions

None for workflow authoring.

## Confidence Level

```text
84 percent
```

## Decision

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```
