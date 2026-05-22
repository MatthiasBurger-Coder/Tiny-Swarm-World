---
name: process-performance-profiler
description: Use to record workflow process metrics such as phase timing, role count, files read, quality commands, repeated governance reads, retries, blockers, critical path and unused parallelization opportunities without replacing required gates.
---

# Skill: Process Performance Profiler

## Mission

Record process-performance diagnostics for governed workflow execution so
future optimization work is evidence-based. Metrics are operational
diagnostics only. They are not proof of correctness and must never replace
required role reviews, STOP rules, S3/S3D checks, D8 quality decisions or
`QUALITY.md` commands.

## Responsibilities

- Record time spent in requirement gates, branch preflight, S3/S3D,
  implementation or documentation slices, quality gates, commit preparation
  and checkpoint push.
- Count roles or local role-review checklists invoked.
- Count files read when the executor can track that count without unsafe
  instrumentation.
- Count quality commands run and classify them as targeted, required or full.
- Record repeated reads of `AGENTS.md`, `QUALITY.md`, routing rules, workflow
  files, context packs and skill registry files.
- Record retry count by Typed Error Router category.
- Record blocker count and blocker category.
- Identify the longest critical path from available slice timing and
  dependency information.
- Record parallelization opportunities not used and the reason, such as file
  lock overlap, architecture lock overlap, missing metadata or quality-gate
  attribution risk.
- Write metrics only under `documentation/workflow/metrics/**`.

## Forbidden

- Do not record secrets, credentials, tokens, personal data, raw evidence
  payloads, prompt content, source-code excerpts or runtime trace payloads.
- Do not block required quality gates to collect metrics.
- Do not mark a slice, workflow, commit, push or release as correct because a
  metric looks healthy.
- Do not introduce telemetry services, external dependencies, background
  agents or build plugins.
- Do not execute product code, parser code, Joern, BTM, replay, graph or UI
  performance tests from this process profiler.

## Inputs

- active workflow version and slice metadata
- execution report
- S3/S3D results
- role-review or subagent routing notes
- quality-gate command evidence
- checkpoint commit and push outcomes
- Typed Error Router retry and blocker records

## Output Location

Write run reports under:

```text
documentation/workflow/metrics/<workflow-id>-run.md
```

Use stable identifiers and summarize measurements. Do not include raw command
logs when a short command name, duration and result are enough.

## Minimum Report Fields

Each run report should include:

```text
workflowVersion
workflowBranch
runDate
executionProfile
sliceCount
rolesInvoked
filesRead
qualityCommandsRun
repeatedGovernanceReads
typedErrorRetries
blockerCount
longestCriticalPath
parallelizationOpportunitiesNotUsed
diagnosticLimitations
```

## STOP Rules

Stop and report when:

- collecting a metric would require recording secrets, prompt content or raw
  forensic evidence payloads;
- metrics would delay, skip, downgrade or replace a required D8 quality gate;
- a requested metric would require executing untrusted repository code;
- a report would present process speed or low retry count as proof of product,
  workflow or evidence correctness.
