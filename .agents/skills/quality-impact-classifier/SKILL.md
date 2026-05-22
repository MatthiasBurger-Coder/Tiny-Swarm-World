---
name: quality-impact-classifier
description: Classifies changed files and workflow slices into quality-impact levels so the Quality Gate Orchestrator can select required checks from QUALITY.md without weakening mandatory gates or treating failed required checks as optional.
---

# Skill: Quality Impact Classifier

## Mission

Classify the quality impact of a planned or completed slice before selecting
commands. The classifier helps avoid unnecessary full Python gates for verified
documentation-only governance work while preserving strict quality authority
for product, build, contract, test, architecture, runtime and quality-rule
changes.

This skill does not replace `QUALITY.md`, approve failed gates, invent quality
tasks, or decide commit readiness by itself.

## Impact Levels

### DOC_ONLY

Use when changed files are documentation-only and cannot influence product
build, source behavior, runtime behavior, contracts, tests, architecture
rules, branch rules, publication rules or quality policy.

Required checks:

- `git diff --check`
- targeted documentation consistency review
- format validation for changed structured files

### GOVERNANCE_METADATA

Use when changed files affect workflow, process, skill, role, routing,
skill-audit, arc42 or ADR governance but do not affect product source, tests,
build logic, contracts, runtime behavior or `QUALITY.md`.

Required checks:

- `git diff --check`
- targeted skill, role, routing, workflow or registry consistency check
- JSON/YAML/Mermaid validation when applicable
- arc42 or ADR check when governance behavior changes

### PRODUCT_BUILD_AFFECTING

Use when a slice changes any product source, tests, build logic, dependency
verification, generated-code configuration, contracts, runtime wiring,
deployment material, or `QUALITY.md`.

Required checks:

- targeted checks from the active workflow;
- the minimum command from `QUALITY.md`;
- the full local gate from `QUALITY.md` when release readiness, broad behavior,
  build health, architecture or coverage is affected.

### UNKNOWN

Use when the changed file set, command authority or impact cannot be verified.

Required action:

- stop and route through the Typed Error Router or Root Architect path instead
  of guessing.

## Required Inputs

- `QUALITY.md`.
- Active workflow slice metadata.
- Changed file list.
- Python tooling files when quality-command impact is possible.
- CI workflow files when pipeline behavior is changed.
- Routing, process, skill and role files when governance impact is possible.

## Outputs

Return:

```text
qualityImpact=<DOC_ONLY|GOVERNANCE_METADATA|PRODUCT_BUILD_AFFECTING|UNKNOWN>
reason=<evidence-based reason>
requiredCommands=<commands from QUALITY.md or active workflow>
notApplicableCommands=<commands plus reason>
blockingChecks=<checks that must pass before commit or push>
```

## Collaboration Rules

- Run before the Quality Gate Orchestrator selects commands.
- Consult Senior Tester for regression and coverage impact.
- Consult Senior System Architect for architecture, import-linter or boundary
  impact.
- Consult Senior DevOps for Python tooling, CI, Docker, deployment or build tooling
  impact.
- Consult Skill Registry Conflict Auditor when skill, role, routing or
  process-governance ownership changes.

## Forbidden

- Do not mark a failed required gate as optional.
- Do not replace a required Python gate with `git diff --check`.
- Do not invent quality tasks, scripts, CI jobs or quality commands.
- Do not classify product source, tests, contracts, build logic, deployment,
  runtime behavior, dependency verification or `QUALITY.md` changes as
  `DOC_ONLY`.
- Do not treat missing evidence as low impact.

## STOP Rules

Stop when:

- `QUALITY.md` cannot be read;
- changed files are unknown;
- file impact is ambiguous;
- a documented command cannot be verified;
- a workflow or process document conflicts with `QUALITY.md`;
- continuing would require guessing quality authority or task names.
