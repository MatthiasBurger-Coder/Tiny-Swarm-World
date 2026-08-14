# Workflow: Issue #128 — Branch Protection and CI Governance

Workflow id: `issue-128-branch-ci-governance-20260812`

Issue: [#128](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/128)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-128-branch-ci-governance-20260812`

Execution branch: `docs/issue-128-branch-ci-governance-20260812`

Status: `COMPLETED`

## Executive Summary

Document the repository's branch protection, pull-request, review and CI
quality-gate expectations. This workflow defines the intended control model; it
does not mutate GitHub settings or claim that unavailable CI checks already
exist.

## Requirement Clarification Gate

- Original request: execute #128 after #121 and #122, before security/admin
  surface implementation.
- Interpreted intent: create the three governance documents and classify each
  protection/check as required now, recommended, target, not applicable or
  deferred.
- Change type: repository governance documentation.
- Affected process strand: branch -> PR -> checks -> review -> merge.
- Affected architecture area: workflow/quality governance, not runtime code.
- Explicit requirements: create `branch-protection.md`, `ci-quality-gates.md`,
  `pr-review-policy.md`; cover direct-push/PR/check/force-push/deletion,
  history/signatures/scanning decisions, local gate mapping and evidence.
- Implicit requirements: distinguish current GitHub state from target state;
  failed/unverifiable required checks block merge; live actions stay out of CI.
- Assumptions: current `.github/workflows/sonar_check.yml` is reviewed as
  repository evidence, not proof of all required checks.
- Non-goals: direct branch-setting mutation, new CI jobs without a separate
  scoped request, live commands and gate weakening.
- Risks: documented policy diverges from actual settings or requires an
  unavailable SonarQube status.
- Open/blocking questions: actual GitHub protection settings are external and
  not changed here; document as unknown/target when unverifiable.
- Confidence: 92%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
change -> dedicated branch -> PR -> local/CI quality evidence -> review -> merge
```

## Verified Baseline, Scope and Assessments

The three issue-required governance files are absent; `.github/workflows` has a
Sonar-related workflow but that does not establish all required checks. Scope is
documentation only. Python/frontend are not applicable. Resilience means a
failed, unavailable or unverifiable required check blocks merge and cannot be
silently bypassed.

## Ordered Slices

### Slice 01 — Requirement matrix and actual-vs-target baseline

```yaml
slice_id: S128-01
profile: GOVERNANCE
owner: Senior Requirement Engineer
secondary_reviewers: [Branch CI Governance Expert, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-128/requirement_matrix.md, .github/workflows/sonar_check.yml]
affected_modules: [branch and CI governance]
affected_contracts: [required-check status model, local QUALITY.md mapping]
dependencies: [S122-02]
parallel_group: SERIAL-128
file_locks: [.tiny-swarm/evidence/issue-128/requirement_matrix.md]
contract_locks: [branch-protection-status-vocabulary]
architecture_locks: [QUALITY.md-authority]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no runtime change; check quality requirements links
  adr: none expected
stop_conditions: [unknown check documented as active, conflict with QUALITY.md, external setting guessed]
```

Done: all issue bullets map to policy sections and actual/target status.

### Slice 02 — Branch, CI and PR policy documents

```yaml
slice_id: S128-02
profile: GOVERNANCE
owner: Branch CI Governance Expert
secondary_reviewers: [QMS-light Governance Expert, Senior Documentation Engineer, Senior Tester]
affected_files: [documentation/governance/branch-protection.md, documentation/governance/ci-quality-gates.md, documentation/governance/pr-review-policy.md, documentation/README.adoc]
affected_modules: [repository governance documentation]
affected_contracts: [main protection expectations, CI quality contract, review/merge policy]
dependencies: [S128-01]
parallel_group: SERIAL-128
file_locks: [documentation/governance/, documentation/README.adoc]
contract_locks: [branch-policy-contract, ci-quality-contract, review-policy-contract]
architecture_locks: [no-direct-github-mutation]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: link quality/release governance only when verified
  adr: none expected
stop_conditions: [claiming CI exists without evidence, bypass path, unknown mergeability treated as green]
```

Done: all policies classify current/target state, map the canonical local gate,
and document evidence/merge blockers without changing CI or GitHub settings.

## Dependency Graph

`S122-02 -> S128-01 -> S128-02`

## Parallel Execution

No implementation parallelism because the local gate and review evidence are
shared. Isolated worktree required; no live validation. Merge in slice order.
Conflicts: any concurrent branch policy, CI workflow or release governance edit.

## Automatic Work Distribution Policy

Use standard distribution/consolidation evidence. Branch/CI, QMS, quality and
documentation reviewers may advise in parallel, but shared status vocabulary,
`QUALITY.md` references and actual-vs-target claims remain serialized.

## Git Worktree Execution Rule

Use isolated worktree branch `docs/issue-128-branch-ci-governance-20260812`.
Do not mutate GitHub settings or merge a PR from this workflow.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-128/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-128/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S128-01 and final.
- System Architect Reviewer review: S128-01 and final.
- Test / Evidence Reviewer review: S128-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: open/unverifiable governance requirements force
  `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality, Documentation and Handoff

Run `git diff --check`; use the full quality gate only if executable CI or
quality tooling changes. Link #122 QMS and #123 security expectations where
verified. Handoff to #126 includes review/merge and quality evidence policy.

Definition of Done: three governance documents are internally consistent,
honest about actual GitHub/CI state and independently audited.

Arc42 Check Status: quality/release governance references reviewed; no runtime
architecture update expected.

## Scope

Only branch protection, CI quality-gate and PR review policy documentation is in
scope; GitHub settings remain external target state.

## Target Outcome

The change-to-merge control path is explicit and honest about current versus
target checks.

## Architecture Constraints

`QUALITY.md` and existing branch/workflow governance remain authoritative; no
CI or GitHub mutation is hidden in documentation.

## Python Automation Assessment

Not applicable unless a separate executable CI/quality change is approved.

## Frontend Assessment

Not applicable; no UI surface is changed.

## Test Strategy

Verify policy fields, actual/target labels, local gate mapping, links and
`git diff --check`.

## Resilience Requirements

Failed, unavailable or unverifiable required checks block merge; no bypass path
or unknown Sonar status may be represented as green.

## Role and Ownership Map

Branch CI expert owns policy; QMS expert reviews quality relation; Requirement
Engineer owns matrix; Tester checks evidence; Architect validates process fit;
Auditor decides completion.

## Commit and Push Plan

One issue-scoped governance commit; do not mutate GitHub protection or add CI
jobs without a separate authorized change.

## Handoff to workflow execute

Promote only after #121/#122 evidence and isolated branch verification; pass
actual-vs-target check status to #126 and later merge governance.

## Arc42 Check Status

Quality and release-governance references were reviewed; no runtime change is
expected.
