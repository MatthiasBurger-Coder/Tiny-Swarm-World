# Workflow: Issue #153 — Harden Incus/LXD Installation Prerequisites Handbook

Workflow ID: `issue-153-20260809`

Workflow version: `issue-153-v1.0.0`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Source: [GitHub Issue #153](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/153)

## Executive Summary

Harden existing user-facing documentation so operators understand that Incus
or LXD is a host prerequisite for `lxc_native`, is not installed/initialized
by Tiny Swarm World, must be usable without `sudo` from the installer shell,
and must be verified before the governed installation flow.

## Target Picture

One navigable prerequisite section and checklist explain host preparation,
minimal smoke validation, host Docker versus Docker inside managed nodes,
installation order and common recovery actions. Existing documentation is
updated rather than duplicated; no source behavior changes unless a verified
contradiction requires a narrow metadata wording fix.

## Clarification, Baseline and Scope

Upstream dependency: `I151-S07`. Current README, user handbook, installation
guide and troubleshooting already contain significant Incus guidance, so the
first slice must inventory overlap before editing. Requirements are in the
[matrix](requirement-matrix.md). Live smoke is classified as optional and
requires explicit consent; the default workflow uses static/documentation
validation only. Confidence 95%, `READY_FOR_WORKFLOW`.

## Ordered Slices

### Slice 01 — Documentation inventory and matrix freeze

Purpose: compare README, handbook, installation and troubleshooting sections,
identify gaps/duplicates and verify no source change is required.

```yaml
slice_id: I153-S01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior Documentation Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [README.md, documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc, documentation/workflow/issues/issue-153/requirement-matrix.md]
affected_modules: [user-facing installation documentation]
affected_contracts: [prerequisite boundary, no-source-change default]
dependencies: [I151-S07]
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-153/**]
contract_locks: [I153-doc-inventory]
architecture_locks: [host-vs-platform-boundary]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review deployment/constraints/risk sections
  adr: review lxc-native provider and host-boundary decisions
stop_conditions: [documentation contradiction, source behavior mismatch, duplicate owner unclear, upstream audit missing]
```

Done criteria: every criterion maps to an existing section or a specific
minimal documentation gap; source change is explicitly ruled out or blocked.

### Slice 02 — Consolidate hard prerequisite boundary

Purpose: state clearly that Incus/LXD installation, initialization, storage,
network and no-sudo CLI access are host responsibilities and `lxc_native` is
the default provider.

```yaml
slice_id: I153-S02
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior System Architect, Linux Host Preparation, Senior Requirement Engineer]
affected_files: [README.md, documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc]
affected_modules: [prerequisite documentation]
affected_contracts: [host responsibility, Tiny Swarm World responsibility]
dependencies: [I153-S01]
parallel_group: SERIAL-DOC-BOUNDARY
file_locks: [README.md, documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc]
contract_locks: [I153-prerequisite-boundary]
architecture_locks: [incus-native-no-auto-install]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: synchronize verified host/provider boundary
  adr: reference existing decisions only
stop_conditions: [docs imply automatic install, sudo requirement contradicts source, Windows-first instructions added]
```

Done criteria: all three prerequisite statements are prominent, consistent and
linked from the existing installation path.

### Slice 03 — Add ready-for-install checklist and minimal smoke test

Purpose: provide a concise checklist and read-only/minimal Incus smoke command
sequence with explicit live applicability and no automatic execution.

```yaml
slice_id: I153-S03
profile: FULL_PATH
owner: Linux Host Preparation
secondary_reviewers: [Senior Documentation Engineer, Senior System Architect, Senior Tester]
affected_files: [documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc, README.md]
affected_modules: [operator prerequisite checklist/smoke guidance]
affected_contracts: [readiness checklist, optional live smoke state]
dependencies: [I153-S02]
parallel_group: SERIAL-CHECKLIST
file_locks: [documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc, README.md]
contract_locks: [I153-checklist-smoke]
architecture_locks: [no-automatic-live-mutation]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review deployment prerequisite wording
  adr: none
stop_conditions: [smoke commands mutate without warning, command cannot be validated, live success implied]
```

Done criteria: checklist and minimal smoke test exist, use POSIX/Linux/WSL
examples and classify live execution as opt-in.

### Slice 04 — Explain host/node distinction and installation order

Purpose: document host preparation through Incus-managed nodes, Docker inside
nodes, Swarm bootstrap and service deployment without claiming execution.

```yaml
slice_id: I153-S04
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Documentation Engineer, Linux Host Preparation, Senior Requirement Engineer]
affected_files: [documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/arc42/07_deployment_view.adoc]
affected_modules: [installation topology and order documentation]
affected_contracts: [host Docker vs node Docker, order from host to services]
dependencies: [I153-S03]
parallel_group: SERIAL-TOPOLOGY
file_locks: [documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/arc42/07_deployment_view.adoc]
contract_locks: [I153-install-order]
architecture_locks: [lxc-native-deployment-topology]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: synchronize only verified deployment topology
  adr: reference lxc-native ADR
stop_conditions: [host/node responsibility conflated, Multipass/Kubernetes-first drift, order contradicts source]
```

Done criteria: diagram/order matches verified architecture and distinguishes
host Docker used for diagnostics from node-local Docker runtime.

### Slice 05 — Document failure cases and user actions

Purpose: consolidate common Incus daemon/profile/storage/network/group/no-sudo
failures and give bounded recovery actions without broad cleanup commands.

```yaml
slice_id: I153-S05
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Linux Host Preparation, Senior System Architect, Senior Tester]
affected_files: [documentation/user-handbook.adoc, documentation/user_guide/troubleshooting.adoc, documentation/user_guide/installation.adoc, README.md]
affected_modules: [prerequisite troubleshooting]
affected_contracts: [failure classification, safe operator remediation]
dependencies: [I153-S04]
parallel_group: SERIAL-TROUBLESHOOTING
file_locks: [documentation/user-handbook.adoc, documentation/user_guide/troubleshooting.adoc, documentation/user_guide/installation.adoc, README.md]
contract_locks: [I153-failure-actions]
architecture_locks: [no-wildcard-cleanup, guarded-provider-actions]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review risks and deployment safety wording
  adr: none
stop_conditions: [unsafe cleanup instruction, unverified command, failure state hidden]
```

Done criteria: common failures and concrete next actions are documented with
safe scope and no live result claim.

### Slice 06 — Remove duplication and validate documentation

Purpose: reconcile repeated sections, verify POSIX commands/links and run the
documentation/full local checks appropriate to the final diff.

```yaml
slice_id: I153-S06
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior Requirement Engineer, Senior Tester, Senior System Architect]
affected_files: [README.md, documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc, documentation/arc42/07_deployment_view.adoc]
affected_modules: [documentation consistency]
affected_contracts: [single source of user guidance, Linux/WSL examples]
dependencies: [I153-S05]
parallel_group: SERIAL-QUALITY
file_locks: [README.md, documentation/user-handbook.adoc, documentation/user_guide/installation.adoc, documentation/user_guide/troubleshooting.adoc, documentation/arc42/07_deployment_view.adoc]
contract_locks: [I153-doc-consistency]
architecture_locks: [docs-match-verified-source]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final deployment/constraints/risk consistency review
  adr: final reference check
stop_conditions: [contradictory docs, invalid command/link, source behavior change needed, quality blocker unclassified]
```

Done criteria: existing docs are updated without unnecessary duplicates and all
commands/claims are classified as static guidance or optional live validation.

### Slice 07 — Evidence package and independent completion audit

Purpose: audit the ten documentation requirements and complete the full chain.

```yaml
slice_id: I153-S07
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Senior Documentation Engineer]
affected_files: [.tiny-swarm/evidence/issue-153/**]
affected_modules: [issue completion evidence]
affected_contracts: [I153-completion-decision]
dependencies: [I153-S06]
parallel_group: SERIAL-AUDIT
file_locks: [.tiny-swarm/evidence/issue-153/**]
contract_locks: [I153-completion-decision]
architecture_locks: [auditor-independent-from-author]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: final reviewed status
  adr: final status
stop_conditions: [open requirement, duplicate guidance, source change hidden, live claim without evidence]
```

Done criteria: S07 is `PASS`; the complete chain has a final independent audit
and no issue is marked done with open/unverified requirements.

## Dependency Graph

```text
I151-S07 -> I153-S01 -> I153-S02 -> I153-S03 -> I153-S04 -> I153-S05 -> I153-S06 -> I153-S07
```

## Parallel Execution

- Can this workflow run in parallel? No; existing documents overlap and the
  user-facing order/checklist must be coherent.
- Conflicting workflows: handbook, installation, host-preparation or provider
  documentation changes touching the same sections.
- Shared files: README, handbook, installation/troubleshooting docs and arc42 deployment view.
- Shared infrastructure: optional live smoke is serialized and not run by default.
- Requires isolated worktree: yes for every slice.
- Requires serialized live validation: yes if explicitly authorized; otherwise `LIVE_NOT_APPLICABLE`/not run.
- Merge-order constraints: S07 is the final chain audit.

## Automatic Work Distribution Policy

Analyze backend/frontend/runtime/tests/docs/quality/architecture/security
streams; browser React is forbidden. Use real subagents or role fallback and
require distribution/consolidation evidence. Never parallelize overlapping
docs, generated files, unclear commands, live prerequisite actions or safety
guidance. Codex owns final integration.

## Git Worktree Execution Rule

Every slice uses an isolated worktree and verifies branch/locks. Documentation
workers do not execute live Incus or installer commands unless separately
authorized by a later workflow.

## Issue Completion Discipline

- Requirement matrix path: `documentation/workflow/issues/issue-153/requirement-matrix.md`; execution copy `.tiny-swarm/evidence/issue-153/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-153/`.
- Required evidence files: standard six plus documentation inventory, checklist/smoke review, topology/order and failure-action review.
- Requirement Lead review: S01/S07.
- System Architect Reviewer review: S01/S04/S05/S07.
- Test / Evidence Reviewer review: S06/S07.
- Issue Completion Auditor review: S07.
- DONE blocking rule: open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality-Gate Expectations

Use `git diff --check` and, when practical, the full local quality gate exactly
as `QUALITY.md` defines it. A documented smoke command is not live evidence;
live states follow the verification policy.

## Documentation Synchronization and Arc42 Check Status

User handbook, installation/troubleshooting docs, README and arc42 deployment
sections were reviewed. Existing Incus/LXC ADRs remain authoritative; no new
ADR or provider behavior is invented.

## Stop Conditions and Uncertainty Escalation

Stop for contradictory documentation, unverified commands, automatic-install
implication, provider-boundary ambiguity, unsafe cleanup guidance or missing
evidence. Escalate to Documentation Engineer, System Architect and Linux Host
Preparation.

## Definition of Done

All ten requirements are explicitly documented, validated, non-duplicative and
evidenced; no source behavior changed unnecessarily; S07 is `PASS`.

## Handoff to workflow execute

Promote #153 only after I151-S07 and execute S01–S07 serially. This is the last
workflow in the requested chain; completion still requires the independent
Issue Completion Auditor decision.

