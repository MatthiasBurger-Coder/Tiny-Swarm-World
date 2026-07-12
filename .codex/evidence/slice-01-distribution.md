# Slice 01 Automatic Work Distribution

- Workflow ID: `workflow-issue-218-fr01-host-detection-20260712`
- Slice ID: `01`
- Slice title: Dedicated host detection boundary
- Execution profile: `FULL_PATH`
- Chosen mode: `SEQUENTIAL`
- Isolated workflow worktree: yes
- Parallel stream worktrees: no
- Live infrastructure: `NOT_RUN` and forbidden for this slice

## S3 / S3D preflight

- `S3_STATUS`: PASS; workflow worktree clean at execution start.
- `S3_BRANCH`: PASS; active local ref exactly matches the declared workflow branch.
- `S3_SCOPE`: PASS; only Issue #218 FR-1 is released.
- `S3_CLASSIFY`: backend + runtime + documentation + quality + architecture;
  terminal presentation is reviewed as Console/status UI, not browser frontend.
- Context hashes: PASS for all recorded governing and baseline source files.
- S3D metadata: PASS; one concrete slice, no dependencies/cycle, serial group,
  46 allowed path entries, 4 file locks, 2 contract locks, and 2 architecture locks.
- Scope amendment checkpoint: PASS before the existing setup-safety ADR was
  edited. The required narrow amendment path was added, uniqueness and metadata
  were revalidated, and the result was
  `S3D_SCOPE_AMENDMENT=PASS affected_files=39`.
- Pre-implementation contract amendment: the typed result must also replace
  fail-open legacy behavior in the existing preflight port/service and network
  observation port/service. Their exact code and test paths were added before
  product writes, producing 46 allowed path entries. The targeted gate now
  includes both existing application-service suites and the dedicated host
  boundary architecture test.
- Final pre-product-write revalidation:
  `S3D_PRE_IMPLEMENTATION=PASS changed=7 affected_files=46 locks=4/2/2`;
  `git diff --check` also passed.

## Stream decision

| Stream | Decision | Reviewer / execution responsibility |
|---|---|---|
| backend | selected, sequential | Senior Python Automation Developer; Codex integrates |
| frontend | review only | Console/status UI Developer; browser/React N/A |
| tests | selected, sequential with code | Senior Tester / DevOps read-only review |
| runtime | compatibility review only | installer and network-runtime consumers; no live run |
| documentation | selected, sequential | System Architect + Documentation review |
| quality | selected after consolidation | targeted gates, full D8, CI and Sonar |
| architecture | selected before implementation | accepted ADR and hexagonal boundary review |
| security | review only | evidence redaction and no-mutation constraints |

Real Codex subagents were used for requirement, system-architecture,
tester/DevOps, workflow-authoring/Git, and Console/status UI read-only reviews.
The main Codex agent remains the sole write-capable implementation and final
integration owner for this slice.

## Expected touched files

- dedicated host-boundary ADR, arc42 sections, and user CLI usage;
- `domain/preflight/host_environment.py`;
- new `application/ports/host` and `application/services/platform/host` code;
- new `infrastructure/adapters/host` signal readers/detector;
- preflight, installer, OS-type, network-runtime, composition, and CLI consumers;
- FR-1 unit, adapter, integration, CLI, composition, and architecture tests;
- workflow, issue, slice, and ignored issue-completion evidence.

## Conflict and safety analysis

Parallel writes are rejected because the ADR, typed report, detector port,
composition, CLI, installer compatibility, and fixtures share one evolving
contract. The slice also has mandatory regression-first ordering. No shared
migration or database/schema change exists, but those conditions would block
parallelization. Generated-file conflicts, contradictory requirements, unclear
architecture, a Three Amigos unsafe decision, secrets ambiguity, or weakened
safety guards also block parallel work.

No live Incus, Docker, Docker Swarm, PowerShell, Windows Firewall, portproxy,
DNS/hosts, network, service bootstrap, reset, or deployment command is allowed.

## Quality gates

1. Focused host/domain/application/adapter/preflight/network/OS/composition/
   integration/installer/CLI tests.
2. `python3 tools/quality_gate.py arch-lint`.
3. `python3 tools/quality_gate.py arch-tests`.
4. `git diff --check`.
5. `python3 tools/quality_gate.py quality`.
6. Ready PR checks including configured Sonar status before merge.

## Consolidation plan

Codex will implement regression-first in this worktree, incorporate or reject
read-only specialist findings explicitly, run targeted checks before D8, write
`.codex/evidence/slice-01-consolidation.md`, complete the ignored issue evidence
package, obtain independent Three Amigos and issue-completion audit decisions,
create exactly one Slice-01 checkpoint commit, push it, and own PR integration.
