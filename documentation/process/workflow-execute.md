# Workflow Execute Process

Use this process when the user requests `workflow execute`.

## Required References

- `AGENTS.md`
- `QUALITY.md`
- `documentation/process/issue-completion-discipline.md`
- `.agents/prompts/workflow-execute.md`
- `.agents/skills/workflow-executor/SKILL.md`
- `.agents/orchestrator/routing-rules.md`
- active workflow under `documentation/workflow`

## Process

1. Verify the active workflow and branch.
2. Run S3 preflight:
   - `S3_STATUS`: inspect the worktree and classify any existing changes.
   - `S3_BRANCH`: verify the workflow branch is active and has a local ref.
   - `S3_SCOPE`: verify the requested work belongs to the active workflow.
   - `S3_CLASSIFY`: classify the next slice only after status, branch and
     scope are valid.
3. Run S3D orchestration before write-capable work:
   - extract slice metadata, dependencies, affected files, contracts, modules
     and quality gates;
   - build the dependency graph and reject unknown IDs or cycles;
   - verify file, contract, module and architecture locks;
   - choose serial execution when locks overlap.
4. Classify the next slice and route it to the smallest suitable role set.
5. Create or verify the requirement matrix before implementation.
6. Run the Three Amigos or specialist review gate for the slice.
7. Create the automatic distribution decision for the slice.
8. Select sequential or parallel execution.
9. If parallel, create isolated Git worktrees per stream, execute
   stream-specific work, collect stream evidence and consolidate into the main
   workflow branch.
10. If sequential, document why sequential execution was chosen and execute the
   slice in the main workflow branch.
11. Implement only the slice's allowed write scope.
12. Run targeted checks first, then required gates from `QUALITY.md`.
13. Classify failures through the Typed Error Router before retries.
14. Fix in-scope test, quality-gate and SonarQube findings without weakening
    gates. Stop only when the repair would be unsafe, out of scope,
    unverifiable or would bypass quality authority.
15. Inspect `git diff` and `git diff --check`.
16. Create or update consolidation evidence for the slice.
17. Create or update issue-completion evidence under
    `.tiny-swarm/evidence/<workflow-or-issue-id>/` when the slice is
    issue-driven.
18. Run or record `issue-completion-auditor` review before any `DONE` claim.
19. Commit exactly one slice. Multi-slice commits are forbidden.
20. Create or update the PR when the active workflow or publication command
    requires it.
21. Merge only after required gates pass, including SonarQube when configured.
22. Continue with the next workflow or issue after successful merge unless a
    real blocker occurs.
23. When the active workflow requires checkpoint pushes, stage only current-slice files, commit, push the workflow branch, and record the result.

Slice checkpoint push is not `push auto`. Workflow-create publication is also
not `push auto`; workflow-create-only branches stay at guarded branch
publication unless the user explicitly confirms a workflow-documentation-only
PR merge after the workflow-create guard is reported. A later explicit
`push auto` may publish task-scoped implementation changes produced by workflow
execution only through the guarded commit, pull request, green required-checks,
SonarQube when configured, merge and cleanup lifecycle.

## Automatic Work Distribution Policy

During `workflow execute`, Codex must automatically inspect every slice and
determine whether it can be split into specialist execution streams. Codex
must prefer automatic work distribution when the slice contains clearly
separable concerns.

Codex must use real subagents where supported. If real subagents are
unavailable or not visible, Codex must perform an explicit role-based fallback
review in the main execution thread.

Codex must not parallelize unsafe slices. Parallel work must be isolated in
Git worktrees. Codex remains responsible for final consolidation, tests,
evidence, PR and merge readiness.

| Stream | Scope |
|---|---|
| backend | Java/Python backend, domain logic, ports, adapters, service code |
| frontend | UI, UX, frontend components, frontend tests |
| tests | unit, component, integration, acceptance tests, fixtures |
| runtime | Docker, LXD/LXC, install.sh, deployment, CI/CD, platform scripts |
| documentation | arc42, README, workflow.md, ADR, evidence, process documentation |
| quality | SonarQube, linting, coverage, static analysis, quality gate repair |
| architecture | boundaries, module structure, hexagonal architecture, SCA/SCAP constraints |
| security | secrets, permissions, credentials, network exposure, risky automation |

Do not split work if:

- the slice modifies the same files across multiple streams;
- the architectural boundary is unclear;
- the workflow contains contradictory requirements;
- implementation order is mandatory;
- a shared migration step must happen first;
- database/schema changes require strict sequencing;
- generated files would create merge conflicts;
- the Three Amigos gate marks the slice as not safely parallelizable;
- secrets or credentials handling is unclear;
- safety guards would be weakened.

For every slice, create `.codex/evidence/slice-<number>-distribution.md`
before implementation. It must contain workflow id, slice id, slice title,
affected areas, chosen execution mode, selected streams, real subagent use,
fallback review use, Git worktree use, expected touched files/directories,
conflict risks, quality gates to run, consolidation plan and the reason
parallelization was accepted or rejected.

For every implemented slice, create or update
`.codex/evidence/slice-<number>-consolidation.md`. It must contain stream
results, accepted findings, rejected findings with reason, files changed per
stream, conflicts found, conflicts resolved, tests executed, SonarQube
findings and fixes, documentation updates and final integration decision.

## Git Worktree Execution Rule

Parallel execution must use isolated Git worktrees. Each stream must use its
own branch and worktree.

Branch names must follow this pattern:

```text
<workflow-branch>-slice-<number>-<stream>
```

Examples:

```text
feature/workflow-refactor-config-20260613-slice-01-backend
feature/workflow-refactor-config-20260613-slice-01-tests
feature/workflow-refactor-config-20260613-slice-01-docs
```

Stream branches may only be merged back after stream-specific tests pass, file
ownership conflicts are resolved, evidence is written and consolidation review
accepts the changes.

## Validation Checklist

- `workflow execute` does not depend on the user saying "with subagents".
- Requirement matrix exists before implementation.
- Every requirement maps to implementation evidence and verification evidence.
- Required `.tiny-swarm/evidence/<workflow-or-issue-id>/` files exist for
  issue-driven work before `DONE`.
- `issue-completion-auditor` review is recorded before any final `DONE` claim.
- Every slice has distribution evidence before implementation.
- Sequential execution records why parallelization was rejected.
- Parallel execution uses isolated stream worktrees and stream branches.
- Real subagents are used where supported, otherwise fallback role review is
  recorded.
- Three Amigos or specialist review remains mandatory before implementation.
- Codex owns final consolidation and stream workers do not merge directly.
- Required quality gates and SonarQube checks are repaired in scope and never
  bypassed.
- Each slice commit contains exactly one slice.

## Stop Conditions

Stop when the branch, slice metadata, dependency graph, locks, ownership,
quality gate, write scope, failure route, distribution evidence,
consolidation evidence, requirement matrix, issue-completion evidence,
auditor review, stream worktree isolation, PR readiness, merge readiness, or
checkpoint target cannot be verified.
