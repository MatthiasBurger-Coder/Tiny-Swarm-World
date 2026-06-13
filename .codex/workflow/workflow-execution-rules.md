# Workflow Execution Rules

Use this reusable workflow for non-trivial repository work.

Root `AGENTS.md` and `QUALITY.md`, when present, remain authoritative for project-specific safety, architecture, documentation, and verification rules. This file coordinates the reusable Codex team structure and must not override project rules.

## Execution Phases

1. Read-only verification
   - Inspect the task, root project instructions, quality documentation, affected files, build files, relevant documentation, reusable `.codex` role or skill files, and any discovered project-specific role or skill files.
   - Verify exact symbols, modules, build tasks, contracts, schema fields, event fields, and commands before implementation.

2. Slice detection
   - Identify the smallest meaningful implementation or documentation slice.
   - Record dependencies, affected files, role owners, verification commands, and stop conditions.
   - For parallel workflow plans, verify disjoint files, tests, package
     structures, workflow templates, governance files, skill files, agent
     files, architecture decisions, dependencies and live infrastructure state.

3. Role assignment
   - Route slices to the smallest suitable set of subagents or role reviews.
   - Prefer project-specific routing rules when the repository provides them.
   - Use callable subagents only when delegated execution is authorized by the active request or workflow command.
   - If callable subagents are unavailable, perform an explicit local review with the matching role file and report that limitation.
   - When multiple independent workflows are intentionally executed in
     parallel, use one dedicated Git worktree, branch, working directory, PR
     and quality-gate lifecycle per workflow.

4. Implementation
   - Apply only the smallest verified change.
   - Keep changes traceable to the requested task, observed defect, verified architecture rule, quality failure, or documented project decision.

5. Verification
   - Run the narrowest meaningful checks first.
   - Run the applicable quality gate from project quality documentation when required by the slice or commit readiness.
   - Run `git diff` and `git diff --check` before claiming completion.

6. Reporting
   - Report changed files, main changes, executed commands, failures, quality-gate result, known limitations, and blockers.

7. Slice checkpoint push
   - When the project workflow requires checkpoint pushes, run them only after the slice quality gate passed.
   - Stage only current-slice files.
   - Run `git diff --cached --check`.
   - Commit with a slice-scoped message.
   - Push only the current workflow branch to `origin`.
   - Record commit SHA and push result.
   - Do not create or merge a PR, run branch cleanup, run `push auto`, force-push or push to `main`.
   - A later explicit `push auto` may publish any task-scoped repository
     change only through the guarded commit, pull request, green
     required-checks, SonarQube when configured, merge and cleanup lifecycle.

## Parallel Workflow Execution

Parallel workflows may run only when the project-specific governance confirms
independence. Never execute multiple parallel workflows in the same worktree.
Serialize workflows with overlapping files, tests, package structures,
governance artifacts, workflow templates, skill files, agent files,
architecture decisions, dependencies, or shared live infrastructure.

Quality gates, evidence, CI, SonarQube observation, PR remediation and merge
are per workflow branch and per worktree. Merge completed PRs one at a time
after re-checking the latest integration branch state and rerunning affected
tests when a branch is updated.

## Workflow Execute Protocol

When the active command is `workflow execute`, use a discovered
project-specific workflow-executor skill as the active execution protocol. Use
`.codex/skills/workflow-executor/SKILL.md` as the reusable base protocol for
portable context and conflict detection.

Execution order:

1. Locate the active workflow.
2. Read the complete workflow.
3. Identify all slices and dependencies.
4. Assign roles or subagents.
5. Execute one slice at a time.
6. Run required tests and quality checks after each slice.
7. Inspect diffs after each slice.
8. Run the project-defined slice checkpoint push after each successful slice when the active workflow requires it.
9. Stop on unverifiable assumptions, architecture conflicts, missing commands, quality failures, failed checkpoint push, or ambiguity that could change behavior.

## Stop Conditions

Stop and report when:

- a required file, class, method, task, schema, contract, field, or event name cannot be verified exactly;
- source and documentation conflict in a behavior-relevant way;
- a change would fabricate evidence, test data, runtime facts, analysis output, or user-visible behavior;
- a slice would violate verified architecture or service-boundary rules;
- a parallel workflow worktree cannot be created, is dirty, overlaps another
  workflow, or depends on a workflow that has not merged;
- shared live infrastructure would be mutated concurrently;
- merge order matters and cannot be determined safely;
- a quality command cannot be verified from repository documentation or build files;
- continuing would require guessing.
