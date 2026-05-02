# Commit And Push Command

## Command Alias

When the user sends exactly `cc`, treat it as an execution command for this
workflow.

Do not treat `cc` as a request to only explain the workflow. Execute the
repository inspection, quality-gate handling, Git inspection, commit creation,
and push steps below.

## Purpose

Inspect the repository, run the project quality gate first, fix all
quality-gate-related issues that are realistically fixable from the current
codebase, re-run the quality gate until it passes or until remaining blockers
are clearly identified, and only then perform the Git inspection, commit
creation, and push.

The task is not to generate a vague commit message. The task is to produce a
commit that clearly documents:

1. what was changed
2. why it was changed
3. how it was changed
4. which files or components were affected
5. whether bugs were fixed
6. whether new features were introduced
7. whether refactoring, cleanup, structural, or architectural changes were made
8. whether tests were added or adjusted
9. whether any breaking or behavior-relevant changes exist

## Phase 1 - Repository Inspection

Perform these steps before quality-gate or commit work:

1. Inspect the repository structure.
2. Inspect `git status`.
3. Inspect staged and unstaged changes separately.
4. Inspect `git diff`.
5. Inspect `git diff --cached`.
6. Inspect available project scripts, tooling, test setup, and quality tooling.
7. Locate `quality_gate.py`.

## Phase 2 - Quality Gate First

If `quality_gate.py` exists, run it before doing any commit work. If it does
not exist, report that explicitly and do not pretend there is a quality gate.

Use the correct interpreter and project root based on the repository structure.
If the repository defines a preferred virtual environment, runner, or command
convention, use it.

For this project, prefer running from the repository root:

```bash
python3 tools/quality_gate.py quality
```

If `python3` is unavailable but an activated virtual environment provides
`python`, use the repository's documented Python command and explain the
fallback.

Collect the full output of the quality gate, identify concrete failures, fix
all failures caused by the current codebase that are realistically fixable in
scope, and re-run the gate.

Repeat until:

- the quality gate passes, or
- only clearly explainable blockers remain.

### Quality Gate Rules

- Do not skip `quality_gate.py` if it exists.
- Do not pretend it passed if it failed.
- Do not move on to the Git phase before at least one fix-and-rerun cycle was
  completed if errors were found.
- If the quality gate fails because of missing environment dependencies, broken
  tooling, unavailable external resources, or unrelated pre-existing repository
  problems, report that precisely.
- Distinguish clearly between:
  - issues introduced by the current change set
  - pre-existing repository issues
  - environment/tooling issues
- If the gate reveals lint, type, import, architecture, test, or runtime
  issues, fix them in the code where appropriate.
- If tests must be updated because of a real implementation change, do so and
  mention it later in the commit message.
- If fixes require refactoring, keep the refactoring targeted and explainable.
- Preserve intended responsibilities in architecture-sensitive areas such as
  UI, adapters, infrastructure, preview mode, final render mode, mask
  generation, propagation, refinement, ports, and use cases.
- Remove unused imports when the gate reports them.

## Phase 3 - Git Work After Quality Gate Handling

Only after the quality gate has been handled:

1. Inspect the final repository state again with `git status`.
2. Inspect the final diffs again.
3. Write a detailed commit message based only on the actual diff.
4. Stage all relevant changes deliberately.
5. Create the commit.
6. Push to the current branch.

If both staged and unstaged changes exist, handle that deliberately and describe
it in the assessment. Do not include unrelated changes silently.

If Windows Git or IDEA credentials are required for pushing, use the available
project-compatible Git path and report the exact push command and result. Do
not claim push success unless the remote branch is verified.

## Commit Message Rules

- Read the real diff, not only file names.
- Do not invent facts that are not visible in the code changes.
- Do not write generic messages such as:
  - `update code`
  - `fix issues`
  - `small improvements`
- If bugs were fixed, state which faulty behavior was corrected.
- If a feature was introduced, state what it does and why it was added.
- If refactoring was done, explain the structural improvement and its purpose.
- If architectural work was done, explicitly name the affected layer,
  component, adapter, port, UI area, infrastructure concern, or workflow.
- If tests were added or changed, mention what was covered, adapted, or
  repaired.
- If multiple concerns are mixed, group them logically and say so honestly.
- If unrelated changes are present, call that out clearly instead of pretending
  the change set is perfectly clean.
- If quality-gate-related fixes were made, mention that explicitly in the
  commit body.
- If `quality_gate.py` itself was added, fixed, integrated, or changed, mention
  that explicitly if it is visible in the diff.

Use this structure:

```text
<type>: <short precise summary>

What:
- ...

Why:
- ...

Changes:
- ...

Impact:
- ...

Testing:
- ...
```

Allowed commit types:

- `feat`
- `fix`
- `refactor`
- `chore`
- `test`
- `docs`
- `perf`

Choose the most accurate type based on the real change set.

## Execution Rules

- Do not commit before reviewing the actual diff.
- Do not push before the commit was created successfully.
- Do not claim success for any step that failed.
- If commit fails, report the exact error.
- If push fails, report the exact error.
- If the quality gate fails, report the exact error.
- If the quality gate still fails after fixes, explain exactly what remains and
  whether it is a code issue, tooling issue, environment issue, or pre-existing
  repository issue.
- If the quality gate is still failing for unresolved blockers, do not hide that
  fact in the final summary.

## Final Output

After execution, print:

1. whether `quality_gate.py` was found or skipped
2. the exact command used to run it
3. whether the quality gate passed
4. if it failed, the exact reason
5. which fixes were applied because of the quality gate
6. the final commit message
7. the branch name
8. the new commit hash
9. whether the push succeeded

If push fails, report the exact reason and do not pretend success.
If the quality gate fails, report the exact reason and do not pretend success.
If remaining blockers exist, state them explicitly.
