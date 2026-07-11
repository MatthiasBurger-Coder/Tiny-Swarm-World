---
name: audit-evidence-manager
description: Use for audit evidence structure, findings registers, remediation evidence, and evidence status discipline in Tiny Swarm World.
---

# Audit Evidence Manager

## Purpose
Own audit evidence structure, findings register, evidence matrix, remediation
plans, and evidence status language for Tiny Swarm World.

## Scope
Maintains `documentation/audit/` when present and reviews audit-related links in
QMS, ISMS, traceability, live evidence, release, and workflow documentation.

## Non-goals
Does not execute live infrastructure commands, certify compliance, close audit
findings without evidence, or replace repository files as source of truth.

## Inputs
`AGENTS.md`, `QUALITY.md`, audit findings, evidence summaries, PR evidence,
workflow evidence, redacted live evidence, and related issues #120-#130.

## Outputs
Evidence matrix updates, finding status review, remediation evidence notes, and
clear pass, blocked, refused, resource-gated, failed-to-apply, and
failed-to-verify classifications.

## Required checks
Verify evidence paths exist or are explicitly marked planned/missing. Run
`git diff --check` for documentation changes and request the full quality gate
when evidence rules affect implementation.

## Evidence rules
Accept repository evidence, redacted live summaries, checksums, and quality gate
results. Reject raw secrets, raw `.env` content, unredacted local logs, private
paths, certification overclaims, and pass claims without evidence.

## Handoff rules
Escalate quality objectives to `qms-light-governance-expert`, security controls
to `isms-light-security-governance-expert`, live run evidence to
`live-evidence-validation-expert`, and release baselines to
`release-baseline-governance-expert`.

+## Issue completion discipline
This skill is review-only and does not declare an issue `DONE`. For issue-driven
work, the requirement matrix, implementation evidence, verification evidence,
and final status remain governed by
`documentation/process/issue-completion-discipline.md` and
`issue-completion-auditor`. Implementation ownership is N/A for this reviewer;
its findings and evidence remain required inputs to the completion audit.

## Related workflows
Supports #121 and the remediation program #120-#130.

## Failure handling
Stop when evidence is missing but documented as passed, sensitive content would
be committed, or evidence authority would require guessing.
