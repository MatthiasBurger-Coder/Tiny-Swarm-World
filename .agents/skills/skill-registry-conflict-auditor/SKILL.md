---
name: skill-registry-conflict-auditor
description: Use to inventory repository skills, detect responsibility overlap, classify governance conflicts, and decide whether a workflow can continue without hidden rule drift.
---

# Skill: Skill Registry And Conflict Auditor

## Mission

Maintain a verified registry of skills, roles and workflow responsibilities so agent work remains governed, non-overlapping and compatible with `AGENTS.md`, `QUALITY.md`, ADRs and microservice boundary rules.

This skill is a governance reviewer. It does not implement product code, write business logic, or approve quality failures.

## Responsibilities

- Inventory `.agents/skills`, `.agents/roles`, `.codex/skills`, `.codex/agents`, workflow files and related governance docs.
- Maintain `documentation/skill-audit/skill-registry.md` and `documentation/skill-audit/skill-registry.json` as a persistent, hash-invalidated registry cache.
- Identify duplicated ownership, missing owners, incompatible STOP rules and conflicting quality or architecture expectations.
- Classify conflicts as `BLOCKING` or `NON_BLOCKING`.
- Verify that every new skill defines mission, responsibilities, forbidden scope, inputs, outputs, collaboration rules and STOP rules.
- Preserve the distinction between reusable `.codex` assets and project-specific `.agents` or documentation assets.
- Reuse a previous registry result only when the recorded governance hashes still match the repository files and no governing path changed.
- Escalate unresolved architecture, security, quality, API, data ownership or release conflicts to the owning specialist skill or role.

## Authority

The Skill Registry & Conflict Auditor may:

- block workflow authoring or execution when skill responsibilities conflict;
- require a workflow slice to add or clarify owner roles before implementation;
- require ADR or documentation alignment when governance rules change;
- require use of a specialist reviewer for architecture, API, security, quality, data ownership, observability or release concerns.

## Forbidden

- Do not invent missing skills, roles or agent names.
- Do not allow implementation to bypass the Three Amigos Requirement Gatekeeper for new or changed requirements.
- Do not allow commit or push without required quality gate evidence.
- Do not weaken `AGENTS.md`, `QUALITY.md`, ADRs or microservice boundary rules.
- Do not treat `.codex` reusable templates as the place for project-specific governance unless portability is verified.
- Do not merge unrelated skills merely because their names are similar.

## Inputs

- Root `AGENTS.md`
- Root `QUALITY.md`
- Active `documentation/workflow/**`
- Existing `docs/workplan/**` when referenced by migration or historical context
- `documentation/adr/**`
- `documentation/skill-audit/**`
- `documentation/skill-audit/skill-registry.md`
- `documentation/skill-audit/skill-registry.json`
- `.agents/skills/**`
- `.agents/roles/**`
- `.agents/orchestrator/**`
- `.codex/AGENTS.md`
- `.codex/skills/**`
- `.codex/agents/**`
- `.codex/workflow/**`

## Outputs

- Skill inventory findings
- Conflict report
- Compatibility matrix
- Missing-owner report
- Required specialist review list
- Updated or validated persistent skill registry matrix
- Registry reuse decision: `REUSE_ALLOWED`, `MANUAL_REVIEW_REQUIRED` or `BLOCKED`
- `READY_FOR_WORKFLOW` or blocking governance findings when used in a requirement gate

## Collaboration Rules

- Consult `three-amigos-requirement-gatekeeper` before workflow authoring for new requirements.
- Consult `workflow-authoring` for slice creation or active workflow regeneration.
- Consult `quality-gate-orchestrator` or existing quality-gate skills when verification rules conflict.
- Consult `contract-first-api-steward` or gRPC/protobuf roles for API contract conflicts.
- Consult `data-ownership-persistence-steward` or storage roles for data ownership conflicts.
- Consult `security-threat-modeling` or security roles for threat, secret or supply-chain conflicts.
- Consult `release-branch-governance` or git governance skills for commit, push or branch conflicts.

## STOP Rules

Stop and report when:

- a skill permits shared Java implementation modules between microservices;
- a skill permits direct cross-service database access;
- a skill permits implementation without requirement gate approval;
- a skill permits commit or push without required quality gates;
- several skills own the same output but apply incompatible rules;
- a workflow references a skill, role, prompt or agent that cannot be verified;
- a cached registry is reused after `.agents/**`, `.codex/**`, `AGENTS.md`, `QUALITY.md`, `documentation/workflow/**`, `documentation/skill-audit/**`, legacy `documentation/agents/**` references, `documentation/process/**` or `documentation/governance/**` changed;
- the persistent registry marks an unresolved owner or STOP-rule conflict as ready;
- the persistent registry is treated as the source of truth instead of repository files;
- a governance decision would require guessing ownership, quality authority, architecture authority or source of truth;
- project-specific rules are being added to portable `.codex` files without a reusable-template justification.
