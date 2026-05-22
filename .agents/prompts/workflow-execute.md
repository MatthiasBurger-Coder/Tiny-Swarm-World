# Workflow Execute Prompt

Use when the user writes `workflow execute`.

## Required Flow

1. Load root `AGENTS.md`.
2. Load root `QUALITY.md`.
3. Locate the active workflow under `documentation/workflow`.
4. Verify that the active workflow includes a checked `documentation/workflow/workflow.md`.
5. Verify that checked or updated `documentation/arc42/**` documentation exists for the workflow.
6. Load `.agents/skills/workflow-executor/SKILL.md`.
7. Load `.agents/orchestrator/routing-rules.md`.
8. Load `.agents/orchestrator/swarm-orchestrator.md`.
9. Verify the active workflow branch before implementation:

```bash
git branch --show-current
git show-ref --verify --quiet refs/heads/<workflow-branch>
git status --short --branch
```

10. Continue only when the active branch matches the workflow branch recorded by
   the active workflow and the local branch ref exists. If the branch must be
   created or restored, do so only after explicit user approval and rerun the
   ref and active-branch checks before file changes.
11. Load Skill Registry & Conflict Auditor when available.
12. Run Requirement Gate when the request introduces or changes a requirement.
13. Run Skill Conflict Audit before implementation slices.
14. Build or verify the slice plan.
15. Run S3D orchestration: dependency graph, topological sort and file, contract, module and architecture-boundary lock checks.
16. Assign subagents or role reviews.
17. Use Agent Handoff Protocol for owner changes and parallel work.
18. Run required quality gates.
19. Evaluate the required quality decision as `D8`; D8 blocks commit,
   checkpoint push and release readiness on failed build, failed tests,
   architecture violation, missing required documentation, missing workflow
   version or failed required quality gate.
20. After each successful slice, create the `CP_RECORD` defined by
   `documentation/process/workflow-execute.md` with workflow version, slice ID, slice
   title, responsible agent, changed files, quality-gate commands,
   quality-gate result, rollback reference, arc42 update status and ADR update
   status.
21. Run the slice checkpoint push defined by `documentation/process/workflow-execute.md`.
22. After `CP_COMMIT` succeeds, record the actual commit hash and push result.
23. Route asynchronous execution-report findings through `Q11`; Q11 is
   non-blocking by default unless the workflow explicitly declares a regulatory
   or compliance reporting gate as part of D8.
24. Produce a summary with exact validation evidence.
25. Commit or push only when the workflow explicitly allows it and required gates are clean.

## Stop Conditions

Stop when:

- active workflow cannot be identified;
- checked `documentation/workflow/workflow.md` is missing;
- checked or updated arc42 documentation is missing;
- active workflow branch is missing, inactive, or has no local ref;
- skill registry was skipped;
- requirement gate was required but skipped;
- subagent or role ownership is missing;
- S3D cannot verify slice metadata, dependency order or conflict locks;
- handoff rules are missing for parallel work;
- required quality gates fail or cannot be verified;
- D8 fails or cannot be verified;
- commit or push is requested without workflow permission.
- slice checkpoint push would include files outside the current slice;
- slice checkpoint push would push to `main`, create or merge a PR, run `push auto`, run branch cleanup or force-push.
- a slice checkpoint commit would contain multiple slice IDs or no active workflow version.
