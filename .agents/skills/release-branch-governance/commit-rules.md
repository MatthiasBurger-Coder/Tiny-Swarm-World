# Commit Rules

## Required Commit Message Content

- Summary
- Workflow version for workflow-execute slice checkpoint commits
- Slice ID and slice title for workflow-execute slice checkpoint commits
- Why
- What changed
- Changed files
- Responsible agent or reviewed role for workflow-execute slice checkpoint commits
- Added or changed skills
- Updated governance
- Updated prompts or workflow docs
- Validation performed
- Quality-gate result
- Rollback reference
- arc42 update status
- ADR update status
- Risks and follow-ups

## Required Evidence

- changed-file review
- quality gate status
- diff check status
- unresolved risks
- commit scope

## Rules

- Stage explicit files only.
- Do not stage unrelated user-owned changes.
- Do not commit with failed required gates.
- Treat workflow-execute commit readiness as `D8`; failed build, tests, architecture validation, required documentation, workflow version or required quality gates block the commit.
- Q11 report notes are non-blocking by default and must not override a failed D8 result.
- Do not include generated or cache output unless explicitly required.
- A workflow-execute checkpoint commit must represent exactly one slice.
- Do not combine multiple slice IDs in one checkpoint commit.
- No multi-slice commits.
- Do not create rollback claims without a verified commit or file-level rollback reference.

## STOP Rules

Stop when:

- commit message is incomplete;
- required quality evidence is missing;
- staged files include unrelated changes;
- commit would mix unrelated scopes.
