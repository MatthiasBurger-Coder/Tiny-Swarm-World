# Skill Registry

## Status

```text
CURRENT_AFTER_SLICE_05
```

This is the canonical Tiny Swarm World skill registry path. Repository files
remain the source of truth; this registry is an audit and navigation artifact.

## Authority

- Root engineering authority: `AGENTS.md`.
- Quality authority: `QUALITY.md`.
- Project-specific skills: `.agents/skills/<skill-name>/SKILL.md`.
- Reusable Codex skills: `.codex/skills/<skill-name>/SKILL.md`.
- Owner map: `documentation/skill-audit/owner-map.md`.
- Organigramm: `documentation/skill-audit/organigramm.md`.

## Current Registry Decision

- Required Tiny Swarm World project skills use the discoverable
  `.agents/skills/<skill-name>/SKILL.md` format.
- Grouped `.md` files under category directories are non-authoritative unless a
  later workflow changes local skill discovery.
- `.codex` skills remain reusable fallback or portable team assets, not the
  place for project-specific Tiny Swarm World policy.
- The removed `microservice-senior-expert` route is replaced by Senior System
  Architect plus `service-decomposition-bounded-context`,
  `microservice-runtime-readiness-expert`,
  `microservice-migration-safety-gate`, and `contract-governance-expert`.

## Current Counts

- Project-specific discoverable skills: 122.
- Reusable `.codex` skills: 6.
- Canonical required Tiny Swarm World skills: 47.
- Removed stale microservice-specific artifacts: 4.

## Verification

Refresh this registry after `.agents/**`, `.codex/**`, `AGENTS.md`,
`QUALITY.md`, `documentation/workflow/**`, `documentation/skill-audit/**` or
process documentation changes.
