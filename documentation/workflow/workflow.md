# Workflow: Complete SonarCloud remediation in bounded batches

Version: `workflow-sonarcloud-remediation-v3.0.0`
Workflow ID: `workflow-sonarcloud-remediation-20260718`
Branch: `fix/workflow-sonarcloud-remediation-20260718`
Status: `READY_FOR_EXECUTION`
Requirement authority: `documentation/epics/sonarcloud-remediation.md`

## Executive Summary

Resolve the authorized 329 SonarCloud finding keys without a bulk edit. Slice 01 validates the frozen 329-key baseline and assigns every authorized key to exactly one later slice. Remote additions, removals, or status changes are recorded as drift and never alter the authorized set. The remaining 32 slices are rule-specific and bounded: 11 S3415 batches of <=20, 10 S5778 batches of <=10, and 11 batches for every remaining rule family.

## Requirement Clarification Gate

| Field | Decision |
|---|---|
| Original request | Solve all 329 findings in this workflow. |
| Explicit requirements | Every baseline issue key must be assigned, repaired, verified, and remotely confirmed; no pilot-only scope. |
| Non-goals | Suppressions, quality-profile changes, exclusions, blind replacement, live infrastructure. |
| Risk | Some findings require a design or behavior decision and must block rather than be guessed. |
| Decision | READY_FOR_WORKFLOW; each blocked key remains explicit and prevents final DONE. |

## Scope and Architecture

Only files under `tests/**` that are named by the frozen batch manifest may change. Product source, CI/Sonar configuration, infrastructure, suppressions, exclusions, and every non-test file are forbidden in this workflow. A baseline key located outside `tests/**` is recorded as `BLOCKED_NON_TEST_SCOPE` and requires a successor workflow with explicit architecture review. Arc42 is checked per slice; ADRs are required only for durable architecture decisions.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/requirement_matrix.md`
- Required evidence path: `.tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/`
- Required evidence files: baseline, per-slice manifests, implementation summaries, changed-files, test results, risks, acceptance checklist.
- Requirement Lead review: required.
- System Architect Reviewer review: required.
- Test / Evidence Reviewer review: required.
- Issue Completion Auditor review: required before final DONE.
- DONE blocking rule: any unassigned, open, failed, or unverifiable issue key yields INCOMPLETE, BLOCKED, or FAILED.

## Test Strategy

Each implementation slice runs changed-module tests, `git diff --check`, `python3 tools/quality_gate.py quality`, and remote SonarCloud branch analysis. S3415 repairs must preserve expressions/messages via AST comparison. S5778 repairs require semantic test review. The final audit compares all baseline keys against remote issue status.

## Ordered Slices

### Slice 01: Refresh complete SonarCloud baseline and batch manifests

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Requirement Engineer"
secondary_reviewers: ["Senior System Architect", "Senior Python Automation Developer", "Senior Tester"]
affected_files: [".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**", ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"]
affected_modules: []
affected_contracts: ["complete issue inventory and deterministic batch manifests"]
dependencies: []
parallel_group: "serial-01"
file_locks: ["workflow evidence"]
contract_locks: ["SonarCloud issue baseline"]
architecture_locks: ["no source/configuration changes"]
quality_gates:
  targeted: ["JSON validation", "git diff --check"]
  required: ["git diff --check"]
documentation: {arc42: "checked", adr: "not required"}
stop_conditions: ["baseline is incomplete or inconsistent", "a manifest exceeds its batch limit"]
```

Validates the frozen 329 authorized keys against the remote API, records remote drift separately, and creates complete issue-key manifests only for those 329 keys; no source edit is allowed. Every key outside `tests/**` is marked `BLOCKED_NON_TEST_SCOPE`, is not assigned to a repair slice, and blocks the final DONE claim.
### Slice 02: S3415 assertion-order batch 1 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "tests/** paths named by the frozen baseline manifest only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-02"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue is outside tests/** or needs a behavior/configuration/architecture change"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 03: S3415 assertion-order batch 2 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-03"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 04: S3415 assertion-order batch 3 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-04"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 05: S3415 assertion-order batch 4 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-05"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 06: S3415 assertion-order batch 5 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-06"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 07: S3415 assertion-order batch 6 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-07"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 08: S3415 assertion-order batch 7 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-08"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 09: S3415 assertion-order batch 8 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "09"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-09"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 10: S3415 assertion-order batch 9 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "10"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-10"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 11: S3415 assertion-order batch 10 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "11"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-11"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 12: S3415 assertion-order batch 11 of 11

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3415`, up to 20 issues.

```yaml
slice_id: "12"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-12"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3415 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 13: S5778 exception-test batch 1 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "13"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-13"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 14: S5778 exception-test batch 2 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "14"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-14"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 15: S5778 exception-test batch 3 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "15"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-15"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 16: S5778 exception-test batch 4 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "16"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-16"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 17: S5778 exception-test batch 5 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "17"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-17"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 18: S5778 exception-test batch 6 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "18"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-18"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 19: S5778 exception-test batch 7 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "19"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-19"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 20: S5778 exception-test batch 8 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "20"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-20"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 21: S5778 exception-test batch 9 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "21"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-21"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 22: S5778 exception-test batch 10 of 10

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5778`, up to 10 issues.

```yaml
slice_id: "22"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-22"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5778 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 23: python:S8495 rule-family batch (4 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S8495`, up to 4 issues.

```yaml
slice_id: "23"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-23"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S8495 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 24: python:S3776 rule-family batch (5 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3776`, up to 5 issues.

```yaml
slice_id: "24"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-24"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3776 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 25: python:S1192 rule-family batch (4 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S1192`, up to 4 issues.

```yaml
slice_id: "25"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-25"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S1192 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 26: python:S7504 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S7504`, up to 1 issues.

```yaml
slice_id: "26"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-26"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S7504 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 27: python:S8786 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S8786`, up to 1 issues.

```yaml
slice_id: "27"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-27"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S8786 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 28: python:S2187 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S2187`, up to 1 issues.

```yaml
slice_id: "28"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-28"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S2187 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 29: python:S5863 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S5863`, up to 1 issues.

```yaml
slice_id: "29"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-29"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S5863 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 30: python:S3626 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S3626`, up to 1 issues.

```yaml
slice_id: "30"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-30"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S3626 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 31: python:S1172 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S1172`, up to 1 issues.

```yaml
slice_id: "31"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-31"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S1172 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 32: python:S107 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S107`, up to 1 issues.

```yaml
slice_id: "32"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-32"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S107 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.

### Slice 33: python:S1313 rule-family batch (1 issues)

Purpose: resolve only the issue keys assigned by the baseline manifest for `python:S1313`, up to 1 issues.

```yaml
slice_id: "33"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers:
  - "Senior Requirement Engineer"
  - "Senior System Architect"
  - "Senior Tester"
affected_files:
  - "baseline-manifest-listed files only"
  - ".tiny-swarm/evidence/workflow-sonarcloud-remediation-20260718/**"
  - ".codex/evidence/workflow-sonarcloud-remediation-20260718/**"
affected_modules: []
affected_contracts:
  - "SonarCloud issue-key manifest"
  - "preservation of behavior and test semantics"
dependencies: ["01"]
parallel_group: "serial-33"
file_locks:
  - "manifest-listed paths"
contract_locks:
  - "rule python:S1313 semantics"
architecture_locks:
  - "no out-of-scope behavior or configuration changes"
quality_gates:
  targeted:
    - "changed-module tests"
    - "git diff --check"
  required:
    - "python3 tools/quality_gate.py quality"
    - "SonarCloud branch analysis"
documentation:
  arc42: "checked; update only if source behavior changes"
  adr: "required only for a durable architecture decision"
stop_conditions:
  - "issue mapping or safe repair is ambiguous"
  - "the issue needs a behavior/configuration/architecture change outside the batch"
  - "a required gate fails"
```

Done criteria: every manifest-listed issue key is resolved in remote analysis; deferred or blocked keys remain explicitly open and prevent a DONE claim for this slice.


## Dependency Graph

```text
01 -> 02..33
02..33 -> final audit after all preceding slices are complete
```

## Parallel Execution

- Can this workflow run in parallel? No by default.
- Conflicting workflows: any workflow touching the same issue key or source file.
- Shared files: baseline manifests, workflow evidence, and potentially test modules.
- Shared infrastructure: SonarCloud branch analysis.
- Requires isolated worktree: yes.
- Requires serialized live validation: remote analysis is serialized; no live infrastructure is allowed.
- Merge-order constraints: Slice 01 first; then repair slices in manifest order; final audit last.

## Automatic Work Distribution Policy

For every slice, create `.codex/evidence/workflow-sonarcloud-remediation-20260718/slice-<number>-distribution.md` before work and a consolidation record after work. Codex evaluates backend, tests, documentation, quality, architecture, runtime, frontend, and security streams. Parallel work is forbidden for overlapping files, unclear semantics, shared manifests, unknown secrets, or a Three Amigos rejection. Real subagents are used where safe; otherwise record role-based fallback. Codex remains integration owner.

## Git Worktree Execution Rule

Use only this workflow branch and an isolated worktree. Each slice receives one checkpoint commit containing only that slice. No worker merges directly; no PR merge, cleanup, or force push occurs during checkpoint publication.

## Definition of Done

All 329 baseline issue keys are assigned exactly once, repaired without forbidden scope changes, pass local quality, and are confirmed resolved by SonarCloud. Any remaining key means this workflow is not DONE.
