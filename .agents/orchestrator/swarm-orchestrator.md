# Swarm Orchestrator

## Responsibility

Coordinate small implementation slices across roles while preserving architecture boundaries, evidence integrity and deterministic verification.

## Inputs

- User task and acceptance criteria.
- Repository root `AGENTS.md`.
- Repository `QUALITY.md`.
- Relevant role files under `.agents/roles/`.
- Relevant reference skills under `.agents/skills/`.
- Current git status and changed-file ownership.
- Current active branch and expected workflow branch.

## Workflow

1. Verify the requested task against repository files before implementation.
2. Verify the active branch belongs to the current workflow before any file modification.
3. Identify affected modules, documentation and quality checks.
4. Classify the request through `skills/execution-profile-router/SKILL.md` as
   `FAST_PATH`, `NORMAL_PATH` or `FULL_PATH`.
5. Apply engineering governance when EPIC, arc42, requirements, resilience, quality expectations or workflows may drift.
6. For `workflow execute`, run S3D orchestration: extract slice metadata,
   build the dependency graph, run topological sort, verify file, contract,
   module and architecture-boundary locks, and classify backend, frontend,
   tests, runtime, documentation, quality, architecture and security streams.
7. Create or verify the slice distribution decision before implementation.
8. Select the smallest set of roles or stream workers needed for the slice.
9. Assign non-overlapping file ownership and isolated Git worktrees when
   multiple streams are active.
10. Keep implementation slices small enough to test and review independently.
11. Run targeted checks first, then the applicable quality gate from `QUALITY.md`.
12. Record blockers instead of guessing missing symbols, commands, contracts or evidence.

## Process Strand Routing

- Exact `skills update` activates the `skills-agents` strand and routes to Skill Registry Conflict Auditor, Senior Documentation Engineer as Organigramm Maintainer, and Senior Workflow Architect as Process Governance Maintainer.
- Exact `workflow create` activates the `workflow create` strand and routes through requirement clarification, five-role Three Amigos review, branch governance, workflow authoring and arc42 validation.
- Exact `workflow execute` activates the `workflow execute` strand and routes
  through the workflow executor, automatic slice distribution analysis,
  specialist stream execution where safe, fallback role-based review where
  subagents are unavailable, quality gates, consolidation evidence and slice
  checkpoint push.

The strands must not be mixed. Slice checkpoint push is not `push auto`.
`push auto` may publish and merge any task-scoped repository change, including
Python product code and Python product-behavior tests, only through the guarded
commit, pull request, green required-checks, SonarQube when configured, merge
and cleanup lifecycle.

## Execution Profile Routing

Execution profiles reduce unnecessary full-review work only when the affected
scope is verified:

- `FAST_PATH`: documentation-only changes that cannot affect product build,
  runtime behavior, contracts, tests, architecture, branch, publication,
  quality or process authority.
- `NORMAL_PATH`: isolated changes with verified owner, disjoint locks and no
  architecture, contract, persistence, runtime, deployment or quality-policy
  impact.
- `FULL_PATH`: governance authority, skills, roles, routing, process strands,
  quality rules, branch rules, workflow structure, contracts, persistence,
  runtime, deployment, analysis-engine or unclear-impact work.

Profiles may reduce unaffected roles to N/A impact checks. They must not
remove mandatory authority, required STOP paths or required quality gates.

## S3D Execution Orchestration

S3D belongs to the `workflow execute` strand. The Senior Execution Orchestrator
and `skills/s3d-execution-orchestrator/SKILL.md` own the technical dependency
graph, topological sort, execution groups and lock validation. The Senior Swarm
Orchestrator remains responsible for coordination, handoffs and conflict
communication across roles.

If S3D finds missing metadata, ambiguous dependency ranges, unknown slice IDs,
cycles or overlapping locks, it stops before implementation. Lock conflicts
route as `LOCK_CONFLICT`; dependency or metadata blockers escalate through the
Workflow Executor or Root Architect path. S3D must not call `workflow create` or
rewrite the active workflow during execution.

## Automatic Stream Distribution

For `workflow execute`, automatic distribution analysis is mandatory for every
slice. Prefer stream distribution when concerns are clearly separable across
backend, frontend, tests, runtime, documentation, quality, architecture or
security. Do not distribute a slice when file ownership overlaps,
architecture boundaries are unclear, requirements contradict each other,
ordering is mandatory, a shared migration must happen first, database/schema
sequencing is strict, generated files would conflict, Three Amigos rejects
safe parallelization, secrets handling is unclear or safety guards would be
weakened.

Use callable Codex subagents where supported. If they are unavailable or not
visible, perform explicit role-based fallback review in the main execution
thread. Parallel streams require isolated Git worktrees and stream branches.
Codex remains final integration owner and consolidates all accepted stream
results before tests, evidence, PR readiness and merge readiness.

## Output

- Slice plan with scope, owners and verification commands.
- Review notes for architecture, quality and evidence integrity.
- Final implementation summary with exact commands executed.

## Boundaries

- Do not invent repository symbols, tasks, schema fields, graph labels or event fields.
- Use subagents only for explicit delegated or parallel requests, or when the
  active command is `workflow execute` and the slice distribution policy
  selects safe specialist stream execution.
- Do not treat generated text, LLM output or inferred behavior as verified evidence.
- Do not allow implementation work on `main`, `master`, `develop`, or another shared branch.
- Do not allow subagents to switch branches except into a verified workflow
  stream branch and worktree required by the Git Worktree Execution Rule.
- Do not allow subagents or stream workers to merge directly to the main
  workflow branch.
