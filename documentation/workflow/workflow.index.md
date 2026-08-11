# Multi-Issue Workflow Index — #163 → #156 → #197 → #152 → #144 → #146 → #147 → #148 → #145 → #151 → #153

Workflow family: `issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Status: `READY_FOR_WORKFLOW`

Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`

Baseline commit at authoring: `b8c64eaa50839fcbf4581ca819286ad13ee88300`

This index is the multi-issue entry point. The existing completed
`documentation/workflow/workflow.md` for Issue #217 is preserved as the
previous active workflow record. The issue-local workflows below are not
executed implicitly; `workflow execute` must receive an explicit promotion or
an executor extension for the selected indexed path.

## Requirement Clarification and Three-Amigos Decision

- Original request: `workflow create #163 → #156 → #197 → #152 → #144 → #146 → #147 → #148 → #145 → #151 → #153; vollständig die maximale Anzahl der Slice erstellen, damit die Änderungen schrittweise vollständig sind.`
- Interpreted intent: create a complete, highly granular, executable planning
  chain for all eleven GitHub issues in the exact supplied order; do not
  implement product changes or run live infrastructure during authoring.
- Change type: multi-issue implementation workflow authoring with requirement
  traceability, architecture governance, performance evidence, console UX and
  user documentation synchronization.
- Affected process strand: `workflow-create-to-workflow-execute`.
- Affected architecture areas: Python hexagonal application/infrastructure
  boundaries, deployment port resolution, async setup orchestration, bounded
  node concurrency, stack verification state, installer bootstrap, terminal
  reporting and Incus prerequisite documentation.
- Explicit requirements: every requirement and acceptance criterion in Issues
  #163, #156, #197, #152, #144, #146, #147, #148, #145, #151 and #153 must be
  represented in an issue-local matrix and mapped to implementation and
  verification slices.
- Implicit requirements: stable evidence identity, no silent scope reduction,
  preservation of LiveConsent fail-closed behavior, deterministic output and
  aggregation, Linux/WSL-only examples, no RabbitMQ reintroduction, no
  Kubernetes-first drift, and independent completion-auditor decisions.
- Assumptions: the current public GitHub issue bodies are the requirement
  authority; the repository baseline is the checked commit above; no live
  Docker, Swarm, Incus, LXC, networking, Socat, service-bootstrap or Selenium
  command is needed for authoring or default verification; local quality gates
  remain authoritative for local completion.
- Non-goals: implementation during `workflow create`, issue mutation, PR
  creation/merge, automatic LXD/Incus installation, Traefik redesign, new
  service boundaries without an ADR, heavyweight benchmarking, and unrelated
  backlog cleanup.
- Risks: issue bodies or remote Sonar state can drift; performance results are
  environment-dependent; async parallelism can weaken safety boundaries;
  direct-published-port mappings can confuse internal target ports; console
  output can hide diagnostic context; existing documentation may overlap.
- Open questions: exact implementation locations for new performance-evidence
  and WSL-Socat adapter modules are selected by the architecture slice from
  verified package boundaries before implementation. This is non-blocking
  because the parent packages and ports are verified and the selection is a
  required slice output.
- Blocking questions: none for workflow authoring. A later implementation
  slice becomes `BLOCKED` if the issue body changes, a required path or
  contract cannot be verified, or an architecture decision is needed but not
  approved.
- Confidence: 94%.
- Decision: `READY_FOR_WORKFLOW`.

The four mandatory Three-Amigos perspectives are recorded in every issue-local
workflow: Senior Requirement Engineer, Senior System Architect, Senior Python
Automation Developer and Senior Tester. The chain also uses Senior Workflow
Architect, Senior Documentation Engineer, quality-gate governance, arc42
governance, issue-completion-auditor and Console/status UI review where the
verified issue scope requires them. No browser React review is applicable.

## Execution Order

The order is intentionally serialized across issues because the user supplied
an explicit dependency chain. Internal parallelism is allowed only inside an
issue workflow after its baseline slice, and only where the issue-local
workflow explicitly declares disjoint locks. Each issue's final audit slice is
the prerequisite for the next issue's first slice.

| Order | Issue | Workflow ID | Workflow | Context pack | Requirement matrix | Slices | Depends on | Status |
|---:|---:|---|---|---|---|---:|---|---|
| 01 | #163 | `issue-163-20260809` | [workflow](issues/issue-163/workflow.md) | [md](issues/issue-163/context-pack.md) / [json](issues/issue-163/context-pack.json) | [matrix](issues/issue-163/requirement-matrix.md) | 5 | none | READY_FOR_WORKFLOW |
| 02 | #156 | `issue-156-20260809` | [workflow](issues/issue-156/workflow.md) | [md](issues/issue-156/context-pack.md) / [json](issues/issue-156/context-pack.json) | [matrix](issues/issue-156/requirement-matrix.md) | 9 | #163 final audit | READY_FOR_WORKFLOW |
| 03 | #197 | `issue-197-20260809` | [workflow](issues/issue-197/workflow.md) | [md](issues/issue-197/context-pack.md) / [json](issues/issue-197/context-pack.json) | [matrix](issues/issue-197/requirement-matrix.md) | 6 | #156 final audit | READY_FOR_WORKFLOW |
| 04 | #152 | `issue-152-20260809` | [workflow](issues/issue-152/workflow.md) | [md](issues/issue-152/context-pack.md) / [json](issues/issue-152/context-pack.json) | [matrix](issues/issue-152/requirement-matrix.md) | 6 | #197 final audit | READY_FOR_WORKFLOW |
| 05 | #144 | `issue-144-20260809` | [workflow](issues/issue-144/workflow.md) | [md](issues/issue-144/context-pack.md) / [json](issues/issue-144/context-pack.json) | [matrix](issues/issue-144/requirement-matrix.md) | 8 | #152 final audit | READY_FOR_WORKFLOW |
| 06 | #146 | `issue-146-20260809` | [workflow](issues/issue-146/workflow.md) | [md](issues/issue-146/context-pack.md) / [json](issues/issue-146/context-pack.json) | [matrix](issues/issue-146/requirement-matrix.md) | 6 | #144 final audit | READY_FOR_WORKFLOW |
| 07 | #147 | `issue-147-20260809` | [workflow](issues/issue-147/workflow.md) | [md](issues/issue-147/context-pack.md) / [json](issues/issue-147/context-pack.json) | [matrix](issues/issue-147/requirement-matrix.md) | 6 | #146 final audit | READY_FOR_WORKFLOW |
| 08 | #148 | `issue-148-20260809` | [workflow](issues/issue-148/workflow.md) | [md](issues/issue-148/context-pack.md) / [json](issues/issue-148/context-pack.json) | [matrix](issues/issue-148/requirement-matrix.md) | 7 | #147 final audit | READY_FOR_WORKFLOW |
| 09 | #145 | `issue-145-20260809` | [workflow](issues/issue-145/workflow.md) | [md](issues/issue-145/context-pack.md) / [json](issues/issue-145/context-pack.json) | [matrix](issues/issue-145/requirement-matrix.md) | 7 | #148 final audit | READY_FOR_WORKFLOW |
| 10 | #151 | `issue-151-20260809` | [workflow](issues/issue-151/workflow.md) | [md](issues/issue-151/context-pack.md) / [json](issues/issue-151/context-pack.json) | [matrix](issues/issue-151/requirement-matrix.md) | 7 | #145 final audit | READY_FOR_WORKFLOW |
| 11 | #153 | `issue-153-20260809` | [workflow](issues/issue-153/workflow.md) | [md](issues/issue-153/context-pack.md) / [json](issues/issue-153/context-pack.json) | [matrix](issues/issue-153/requirement-matrix.md) | 7 | #151 final audit | READY_FOR_WORKFLOW |

Total: **74 granular executable slices**.

## Shared #152 performance evidence contract

The executed #152 contract is documented at
`documentation/process/performance-evidence-contract.md`. Consumer workflows
record local or mocked measurements below
`.tiny-swarm/evidence/<issue-id>/` using the typed schema's issue/workflow/
segment identity, safe context, optional timestamps/duration, counters,
baseline/new values and explicit limitations. Local timing is comparative only
and never a globally absolute benchmark; no external service is required.

| Consumer | Segment ID |
|---|---|
| #144 | `install-readiness-wait` |
| #146 | `lxc-node-install` |
| #147 | `stack-apply-registration` |
| #148 | `installer-bootstrap` |
| #145 | `setup-phase-group` |

## Dependency Graph

```text
I163-S05
  -> I156-S01 -> I156-S09
  -> I197-S01 -> I197-S06
  -> I152-S01 -> I152-S06
  -> I144-S01 -> I144-S08
  -> I146-S01 -> I146-S06
  -> I147-S01 -> I147-S06
  -> I148-S01 -> I148-S07
  -> I145-S01 -> I145-S07
  -> I151-S01 -> I151-S07
  -> I153-S01 -> I153-S07
```

The arrows above represent the required cross-issue order. Each issue-local
workflow contains the complete internal dependency graph and may use only its
declared parallel groups.

## Shared Governance Contract

- Every executable slice uses an isolated Git worktree and verifies the
  workflow branch before writing.
- `workflow execute` automatically analyzes every slice for backend, frontend,
  tests, runtime, documentation, quality, architecture and security streams;
  real Codex subagents are used where available, otherwise an explicit
  role-based fallback is recorded.
- Before implementation or external action,
  `.codex/evidence/slice-<number>-distribution.md` is required; implemented
  slices additionally require `.codex/evidence/slice-<number>-consolidation.md`.
- Issue-driven completion requires
  `.tiny-swarm/evidence/<workflow-or-issue-id>/requirement_matrix.md`,
  `implementation_summary.md`, `changed_files.md`, `test_results.md`,
  `remaining_risks.md` and `acceptance_checklist.md`, plus the issue-specific
  evidence named by its workflow.
- Any open, guessed, conflicting or unverified requirement forces
  `INCOMPLETE`, `BLOCKED` or `FAILED`; it can never be reported as `DONE`.
- Local verification uses the exact commands from `QUALITY.md`. Live and
  external states follow `documentation/process/verification-state-policy.md`.
- No workflow authoring slice runs live infrastructure or claims SonarQube,
  Selenium, Docker, Incus, Swarm or installation success without executed,
  redacted evidence.

## Excluded Workflows

No requested issue was excluded. The prior completed Issue #217 workflow is
preserved outside this new indexed chain and is not a dependency of the new
chain.

## Handoff

This index is ready for `workflow execute` only after the executor promotes one
issue-local workflow explicitly and validates its S3/S3D locks. The first
executable workflow is Issue #163; no executor may infer a different starting
issue from the index.
