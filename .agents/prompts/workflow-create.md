# Workflow Create Prompt

Use when the user writes `workflow create`.

Read-only verification, requirement intake, routing-rule inspection and role selection may occur before branch creation. Mutating workflow creation must not.

## Requirement Clarification Loop

Before authoring or regenerating `documentation/workflow/workflow.md`, run the requirement clarification loop from `documentation/process/workflow-create.md` and `.agents/skills/three-amigos-requirement-gatekeeper/SKILL.md`.

Record:

- Original Request
- Interpreted Intent
- Change Type
- Affected Process Strand
- Affected Architecture Area
- Explicit Requirements
- Implicit Requirements
- Assumptions
- Non-Goals
- Risks
- Open Questions
- Blocking Questions
- Confidence Level
- Decision: `READY_FOR_WORKFLOW`, `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` or `REQUIRES_REFINEMENT`

Ask focused clarification questions when blocking questions remain. Do not create a final workflow and do not release `workflow execute` while blocking questions remain.

Track clarification attempts. Automatic clarification loops are capped at `maxRetries = 3`; after the third unresolved attempt, stop and escalate to the Root Architect with the unresolved blockers and inspected files.

`workflow create` must use five mandatory roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior React Frontend Developer and Senior Tester.

## Required Branch-First Flow

1. Load root `AGENTS.md`.
2. Load root `QUALITY.md`.
3. Load `.agents/skills/workflow-authoring/SKILL.md`.
4. Load `.agents/orchestrator/routing-rules.md`.
5. Load `.agents/skills/git-branch-strategy/SKILL.md`.
6. Load `.agents/skills/workflow-conflict-resolution/SKILL.md`.
7. Load `.agents/skills/release-branch-governance/branch-rules.md`.
8. Verify the Git repository context:

```bash
git rev-parse --show-toplevel
```

9. Check the working tree:

```bash
git status --short
```

10. Stop if the current branch is detached, unclear, or if unrelated or unclear uncommitted changes exist.
11. Generate a dedicated workflow branch name unless the current branch already exactly matches this workflow:

```text
feature/workflow-<short-topic>-<yyyyMMdd>
fix/workflow-<short-topic>-<yyyyMMdd>
docs/workflow-<short-topic>-<yyyyMMdd>
architecture/workflow-<short-topic>-<yyyyMMdd>
```

12. Check local and remote branch-name collisions, choosing the next clear unique suffix when needed.
13. Create and checkout the workflow branch when no matching workflow branch is active:

```bash
git checkout -b <workflow-branch>
```

14. Verify that the branch ref exists and that it is active:

```bash
git show-ref --verify --quiet refs/heads/<workflow-branch>
git branch --show-current
```

15. Continue only when the local branch ref exists and the active branch exactly
    matches the workflow branch.
16. Create or regenerate workflow artifacts only after successful branch verification.
17. Build slices, role ownership, quality gates and stop conditions through the workflow-authoring skill.
18. Add the required `## Parallel Execution` workflow section. Default every
    workflow to a required isolated Git worktree, allow parallel execution only
    after Three Amigos confirms independence, and serialize live validation
    unless isolated infrastructure is available.
19. Add the required `## Automatic Work Distribution Policy` and
    `## Git Worktree Execution Rule` sections so `workflow execute`
    automatically analyzes every slice for safe specialist streams, requires
    evidence, uses real subagents where supported, and uses fallback
    role-based review where subagents are unavailable.
20. Validate that `documentation/workflow/workflow.md` and checked or updated `documentation/arc42/**` documentation exist before releasing `workflow execute`.

For microservice migration workflows, record the Three Amigos decision before
workflow authoring continues. The decision must include scope, non-scope,
acceptance criteria, service boundary, contract impact, test impact, risk level
and stop conditions.

## Subagent Rules

- Subagents must verify that the active branch belongs to the current workflow before modifying files.
- Subagents must not switch branches unless the workflow explicitly authorizes that branch operation.
- Subagents must stop before implementation work on `main`, `master`, `develop`, or any shared branch.
- Parallel `workflow execute` streams must use separate worktrees and stream
  branches named `<workflow-branch>-slice-<number>-<stream>`.
- Subagents and stream workers must not directly merge to the main workflow
  branch without Codex consolidation.

## Stop Conditions

Stop when:

- no Git repository is detected;
- the current branch cannot be determined;
- the current branch is detached or unclear;
- unrelated or unclear uncommitted changes exist;
- local or remote branch-name collisions cannot be resolved with a clear unique suffix;
- the workflow branch cannot be created;
- the workflow branch cannot be checked out;
- the workflow branch ref cannot be verified after creation or checkout;
- the active branch after checkout does not match the expected workflow branch;
- workflow rules conflict and cannot be resolved from repository sources;
- creating or modifying workflow artifacts would happen on `main`, `master`, `develop`, or another shared branch.
- blocking requirement questions remain;
- `documentation/workflow/workflow.md` cannot be validated;
- arc42 documentation cannot be checked or updated.

Use this stop report:

```text
STOP: workflow create cannot continue safely.
Reason: <concrete reason>
No workflow files were created before resolving the branch isolation issue.
```
