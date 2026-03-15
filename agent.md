# agent.md
## Mission
Restore Tiny Swarm World to a runnable, reproducible, testable, and maintainable state using the ordered tasks in `TASKLIST.md`.

## Scope
- Python orchestration (`docker/`), shell automation, compose/stack assets, tests, and documentation.
- Incremental remediation from foundation to end-to-end smoke validation.

## Non-goals
- Large architectural rewrite without evidence.
- Feature expansion beyond restoring verified operational goals.

## Working principles
- Prefer minimal, evidence-based changes.
- Preserve working behavior where validated.
- Keep source-code comments in English only.

## Audit-first rule
Before modifying any area, read relevant findings in `AUDIT_REPORT.md` and re-check current files.

## Evidence-before-conclusion rule
Do not mark a task complete without command output and file evidence.

## Minimal-change rule
Implement the smallest change set that satisfies the finding acceptance criteria.

## Validation-before-completion rule
Every task must include runnable validation commands and recorded outcomes.

## Documentation-sync rule
Any behavior/config change must update README/user/system docs in the same task.

## Platform-compatibility preservation rule
Maintain explicit Linux and WSL2 branches where applicable; avoid breaking one platform while fixing another.

## English-comments-only rule
All newly added source comments must be in English.

## Task execution protocol
1. Select next TODO task with dependencies satisfied.
2. Reproduce issue.
3. Implement fix.
4. Run validation commands.
5. Update docs/tests.
6. Commit with task ID in message.

## Task status update protocol
Track task state as TODO -> IN_PROGRESS -> DONE with linked evidence (commands + files).

## Failure handling protocol
If blocked, record blocker details, attempted commands, logs, and propose smallest unblock task.

## Assumption logging protocol
When assumptions are required, write them explicitly and add a validation plan.

## Progress note protocol
After each task, append a short progress note: changed files, commands run, results, next dependency.

## Definition of Done
- All critical/high findings closed or explicitly reclassified with evidence.
- Canonical bootstrap + deploy + smoke test path passes on clean environment.
- `pytest` and smoke checks are reproducible from documented commands.
- Docs reflect implementation and troubleshooting paths.
