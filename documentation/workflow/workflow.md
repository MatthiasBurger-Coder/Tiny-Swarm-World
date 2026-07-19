# Workflow: Skill- und Agent-Governance optimieren

Version: `workflow-skill-agent-governance-v1.0.0`
Workflow ID: `workflow-skill-agent-governance-20260720`
Branch: `feature/workflow-skill-agent-governance-20260720`
Status: `READY_FOR_EXECUTION`
Requirement authority: user request, normalized below; no EPIC was found

## Executive Summary

This workflow inventories and classifies the existing Tiny Swarm World skill,
agent, role, prompt and routing structure, then adds technically enforceable
activation metadata, a Skill Activation Resolver, semantic registry auditing,
compatibility tests and synchronized governance documentation. Existing
process-strand semantics remain unchanged.

## Requirement Clarification Gate

| Field | Decision |
|---|---|
| Original request | Optimize skill and agent governance without changing existing process semantics. |
| Interpreted intent | Separate permanent governance from conditional and external skills; make routing and registry consistency machine-checkable. |
| Change type | Governance, process structure, documentation and test-only compatibility changes. |
| Affected process strand | `workflow execute` will later execute this workflow; it is not `skills update`. |
| Affected architecture area | Agent/skill governance and workflow orchestration boundaries. |
| Explicit requirements | Preserve `workflow create`, `workflow execute`, `push auto`, `skills update`; inventory; classify; resolve activation; audit; regression-test; document evidence. |
| Non-goals | No product runtime implementation, no change to `composition.py`, no live infrastructure, no silent external-skill activation, no process-strand merge. |
| Assumptions | Existing repository files are authoritative; no named EPIC exists; governance-only tests may be added where needed. |
| Risks | Existing registry counts and discoverable entries differ; ambiguous/external legacy skills require explicit decisions. |
| Open questions | Any unresolved ownership, reference or semantic conflict blocks the affected slice and final DONE. |
| Confidence | 92% |
| Decision | `READY_FOR_WORKFLOW` |

## Target Picture

The Command Router remains authoritative for command-strand selection. A
Skill Activation Resolver selects context only after the strand is known and
cannot modify requirements, order, gates, stop conditions, branch rules,
worktrees, evidence rules or completion authority. Core skills remain available;
conditional skills require matching evidence; external skills require explicit
approval and verified project scope.

`src/tiny_swarm_world/infrastructure/composition.py` remains the concrete
runtime composition root. It is inspected as an architecture boundary only and
is forbidden in all implementation write scopes of this workflow.

## Scope and Architecture Constraints

Allowed change areas are `.agents/**`, `.codex/**`,
`documentation/process/skills/**`, `documentation/process/skills-update.md`,
`AGENTS.md`, `.agents/AGENTS.md`, governance-only tests/tools and workflow
evidence. Product source, product-behavior tests, runtime adapters, Docker,
contracts, persistence, analytics and `composition.py` are forbidden.

Root `AGENTS.md`, `QUALITY.md`, issue-completion discipline, existing ADRs and
repository behavior remain authoritative. No skill may weaken Three Amigos,
Requirement Matrix, Evidence, Quality Gates, Issue Completion Auditor or the
publication guard.

## Execution Profile and Required Reviews

`executionProfile=FULL_PATH` because skill ownership, routing, process
semantics, quality gates and publication behavior are affected.

Mandatory roles for every governance decision:

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester

Required governance reviewers:

- Skill Registry Conflict Auditor
- Senior Workflow Architect
- Senior Documentation Engineer
- Issue Completion Auditor before final DONE
- Quality Gate Orchestrator before final DONE

No Console/status UI or browser React reviewer is required; terminal UI and
frontend product behavior are outside scope.

## Ordered Slices

### Slice 01 — Complete inventory and requirement matrix

```yaml
slice_id: "01"
profile: "FULL_PATH"
owner: "Senior Requirement Engineer"
secondary_reviewers: ["Senior System Architect", "Senior Workflow Architect", "Skill Registry Conflict Auditor", "Senior Tester"]
affected_files: ["AGENTS.md", "QUALITY.md", ".agents/**", ".codex/**", "documentation/process/skills/**", "documentation/workflow/**", "documentation/process/issue-completion-discipline.md", "composition.py (read-only boundary)"]
affected_modules: ["skill and agent governance"]
affected_contracts: ["inventory matrix", "requirement matrix"]
dependencies: []
parallel_group: "serial-01"
file_locks: ["current governance inventory"]
contract_locks: ["source-of-truth and discoverability rules"]
architecture_locks: ["composition.py remains runtime wiring root"]
quality_gates:
  targeted: ["inventory completeness", "reference existence checks", "git diff --check"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked; update only if governance boundary changes"
  adr: "required for durable authority or architecture decisions"
stop_conditions: ["incomplete inventory", "unverifiable owner", "unresolved source-of-truth conflict"]
```

Produce the complete matrix and Three-Amigos review record before any
classification or implementation decision.

### Slice 02 — Classification and activation metadata

```yaml
slice_id: "02"
profile: "FULL_PATH"
owner: "Skill Registry Conflict Auditor"
secondary_reviewers: ["Senior Requirement Engineer", "Senior System Architect", "Senior Documentation Engineer"]
affected_files: [".agents/skills/**", ".codex/skills/**", "documentation/process/skills/audit/**"]
affected_modules: ["skill metadata and registry"]
affected_contracts: ["core/conditional/external classification", "activation metadata"]
dependencies: ["01"]
parallel_group: "serial-02"
file_locks: ["skill entrypoints", "registry artifacts"]
contract_locks: ["exactly one primary owner", "external approval rule"]
architecture_locks: ["project identity and workflow authority"]
quality_gates:
  targeted: ["metadata schema validation", "registry consistency"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked"
  adr: "only for changed durable authority"
stop_conditions: ["ambiguous classification", "unowned skill", "silent removal or merge"]
```

Classify every discoverable skill and add semantically complete machine-readable
metadata without deleting or merging content.

### Slice 03 — Skill Activation Resolver

```yaml
slice_id: "03"
profile: "FULL_PATH"
owner: "Senior Python Automation Developer"
secondary_reviewers: ["Senior System Architect", "Senior Requirement Engineer", "Senior Tester"]
affected_files: [".agents/**", ".codex/**", "governance-only resolver tests"]
affected_modules: ["skill activation and command-strand boundary"]
affected_contracts: ["resolver input/output", "mandatory gate immutability"]
dependencies: ["01", "02"]
parallel_group: "serial-03"
file_locks: ["resolver implementation", "resolver tests"]
contract_locks: ["Command Router authority"]
architecture_locks: ["no cross-strand calls", "no gate weakening"]
quality_gates:
  targeted: ["resolver unit tests", "negative external-skill tests"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked; update governance boundary if needed"
  adr: "required if resolver authority changes"
stop_conditions: ["resolver can alter strand, gates, requirements or stop conditions"]
```

### Slice 04 — Internal orchestrator responsibility model

```yaml
slice_id: "04"
profile: "FULL_PATH"
owner: "Senior Workflow Architect"
secondary_reviewers: ["Senior System Architect", "Senior Requirement Engineer", "Skill Registry Conflict Auditor"]
affected_files: [".agents/orchestrator/**", ".agents/prompts/**", "governance-only tests"]
affected_modules: ["Command Router, Resolver, Planner, Lock Coordinator, Execution, Completion, Publication"]
affected_contracts: ["existing public command behavior"]
dependencies: ["01", "02", "03"]
parallel_group: "serial-04"
file_locks: ["orchestrator and routing documentation"]
contract_locks: ["workflow-strand semantics"]
architecture_locks: ["no public command or ordering change"]
quality_gates:
  targeted: ["routing characterization tests"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked; synchronize if responsibility boundary changes"
  adr: "required for durable orchestration architecture"
stop_conditions: ["public behavior drift", "new automatic cross-call", "changed evidence or branch rule"]
```

### Slice 05 — Semantic audit implementation

```yaml
slice_id: "05"
profile: "FULL_PATH"
owner: "Skill Registry Conflict Auditor"
secondary_reviewers: ["Senior Tester", "Senior System Architect", "Senior Documentation Engineer"]
affected_files: ["tools/skill_audit.py", "governance-only audit tests", "documentation/process/skills/audit/**"]
affected_modules: ["semantic registry audit"]
affected_contracts: ["audit error codes", "blocking versus warning policy"]
dependencies: ["02", "03", "04"]
parallel_group: "serial-05"
file_locks: ["audit implementation and registry artifacts"]
contract_locks: ["registry/owner-map/organigramm consistency"]
architecture_locks: ["audit cannot replace independent completion authority"]
quality_gates:
  targeted: ["python3 tools/skill_audit.py", "audit fixture tests"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked"
  adr: "not required unless authority changes"
stop_conditions: ["semantic conflict emitted only as warning", "missing reference not detected"]
```

### Slice 06 — Process-strand compatibility regression tests

```yaml
slice_id: "06"
profile: "FULL_PATH"
owner: "Senior Tester"
secondary_reviewers: ["Senior Requirement Engineer", "Senior System Architect", "Senior Python Automation Developer"]
affected_files: ["governance-only tests/**", ".agents/**", ".codex/**"]
affected_modules: ["workflow create", "workflow execute", "push auto", "skills update"]
affected_contracts: ["command-strand characterization", "gate and evidence invariants"]
dependencies: ["03", "04", "05"]
parallel_group: "serial-06"
file_locks: ["routing and compatibility tests"]
contract_locks: ["existing process semantics"]
architecture_locks: ["no product behavior tests or runtime changes"]
quality_gates:
  targeted: ["compatibility tests", "golden-master routing tests"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked"
  adr: "not required"
stop_conditions: ["any process-strand semantic drift", "missing evidence invariant"]
```

### Slice 07 — Registry and governance documentation synchronization

```yaml
slice_id: "07"
profile: "FULL_PATH"
owner: "Senior Documentation Engineer"
secondary_reviewers: ["Skill Registry Conflict Auditor", "Senior Workflow Architect", "Senior System Architect", "Senior Requirement Engineer"]
affected_files: ["documentation/process/skills/audit/**", "AGENTS.md", ".agents/AGENTS.md", "governance-only documentation"]
affected_modules: ["registry, owner map, organigramm, root routing rules"]
affected_contracts: ["documented and machine-readable governance parity"]
dependencies: ["02", "03", "04", "05", "06"]
parallel_group: "serial-07"
file_locks: ["registry and governance documentation"]
contract_locks: ["authority order and external-skill policy"]
architecture_locks: ["composition.py remains unchanged"]
quality_gates:
  targeted: ["registry parity audit", "reference/link checks"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked or synchronized"
  adr: "required only for durable architecture decisions"
stop_conditions: ["documentation contradicts machine-readable registry", "external skill lacks exception"]
```

### Slice 08 — Final audit and completion handoff

```yaml
slice_id: "08"
profile: "FULL_PATH"
owner: "Issue Completion Auditor"
secondary_reviewers: ["Quality Gate Orchestrator", "Senior Requirement Engineer", "Senior System Architect", "Senior Tester"]
affected_files: [".tiny-swarm/evidence/workflow-skill-agent-governance-20260720/**", ".codex/evidence/**"]
affected_modules: ["completion and evidence governance"]
affected_contracts: ["Definition of Done", "completion authority"]
dependencies: ["01", "02", "03", "04", "05", "06", "07"]
parallel_group: "serial-08"
file_locks: ["final evidence"]
contract_locks: ["issue completion status"]
architecture_locks: ["auditor remains independent"]
quality_gates:
  targeted: ["semantic audit", "all compatibility tests", "evidence completeness"]
  required: ["git diff --check", "python3 tools/quality_gate.py quality"]
documentation:
  arc42: "checked"
  adr: "checked if required by prior slices"
stop_conditions: ["any open requirement, missing evidence, failed gate or unresolved conflict"]
```

## Dependency Graph

```text
01 -> 02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08
```

All slices are serial. Governance files, registry artifacts and routing rules
are shared contracts; Three Amigos must explicitly re-evaluate parallelism
before any future change.

## Parallel Execution

- Can this workflow run in parallel? No; shared governance contracts and required ordering make it serial by default.
- Conflicting workflows: any workflow changing `.agents/**`, `.codex/**`, registry, routing, workflow semantics or `AGENTS.md`.
- Shared files: registry, owner map, organigramm, routing rules, root governance files.
- Shared infrastructure: none; live infrastructure is forbidden.
- Requires isolated worktree: yes.
- Requires serialized live validation: no live validation permitted; all validation is serialized in the workflow worktree.
- Merge-order constraints: slices must complete in order; no slice may be marked complete with unresolved conflicts.

## Automatic Work Distribution Policy

`workflow execute` must analyze every slice for safe specialist stream
decomposition and create `.codex/evidence/slice-<number>-distribution.md`
before implementation. Real subagents are used where available; otherwise an
explicit role-based fallback is recorded. Governance slices are not split when
files, ownership, registry assertions, process semantics, generated artifacts,
secrets handling or safety guards overlap. Consolidation evidence is required
at `.codex/evidence/slice-<number>-consolidation.md`. Codex remains final
integration owner. Backend, runtime and frontend streams are N/A unless later
evidence expands scope; documentation, quality, architecture, security and
tests route to their verified owners.

## Git Worktree Execution Rule

Execution uses the declared workflow branch in an isolated worktree. Any safe
stream must use `<workflow-branch>-slice-<number>-<stream>`. Workers must not
merge directly. Each slice has exactly one slice commit, and no stream may edit
`composition.py` or product implementation files.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/workflow-skill-agent-governance-20260720/requirement_matrix.md`
- Required evidence path: `.tiny-swarm/evidence/workflow-skill-agent-governance-20260720/`
- Required evidence files: `requirement_matrix.md`, `current_skill_inventory.md`, `classification_decisions.md`, `activation_rules.md`, `orchestrator_compatibility_analysis.md`, `semantic_audit_results.md`, `workflow_create_regression.md`, `workflow_execute_regression.md`, `push_auto_regression.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, `implementation_summary.md`.
- Requirement Lead review: required.
- System Architect Reviewer review: required.
- Test / Evidence Reviewer review: required.
- Issue Completion Auditor review: required.
- DONE blocking rule: any open, unverified, conflicting or unevidenced requirement forces `INCOMPLETE`, `BLOCKED` or `FAILED`; `DONE` is forbidden until the auditor returns `PASS`.

## Quality Gates

Required commands are those verified in `QUALITY.md`: `git diff --check` and,
when practical and applicable to the governance changes,
`python3 tools/quality_gate.py quality` executed in WSL/Linux. No live
infrastructure command is permitted.

## Stop Conditions and Uncertainty Escalation

Stop for incomplete inventory, unclear ownership, missing references,
classification ambiguity, resolver authority leakage, process-strand drift,
registry disagreement, failed mandatory gates, missing evidence, product-file
scope expansion, or any contradiction that cannot be resolved from repository
sources. Escalate unresolved governance authority to the Root Architect via
Senior System Architect.

## Definition of Done

All requested discoverable entries are inventoried and classified; resolver and
semantic audit pass; compatibility and characterization tests pass; registry,
owner map, organigramm and root governance documents agree; external skills are
never implicit; mandatory gates and all four process-strand semantics are proven
unchanged; all evidence exists; Issue Completion Auditor returns `PASS`.

## Handoff to workflow execute

Execution may start only on the declared branch after reviewing this workflow,
the context pack, the requirement matrix and the mandatory four-role Three
Amigos decision. Slice 01 must complete before any write-capable classification
or resolver work.

## Arc42 Check Status

Checked relevant Arc42 architecture documentation. The existing architecture
states that `composition.py` remains the concrete runtime wiring root and that
skill governance is separate from product runtime. No Arc42 update is required
for this planning-only workflow; any later change to that boundary requires a
separate architecture decision and workflow.
