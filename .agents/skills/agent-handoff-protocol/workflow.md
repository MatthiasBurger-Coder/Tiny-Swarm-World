# Workflow

## Phase 1 - Identify Handoff Need

Create a handoff when:

- a slice changes owner;
- implementation moves from planning to execution;
- review findings require another owner;
- parallel work is proposed;
- quality, architecture, API, security, data ownership or release evidence must be transferred.

## Phase 2 - Verify Participants

Verify:

- source agent or role exists;
- target agent or role exists;
- source owns the current artifact;
- target owns the next action;
- no reviewer is the sole implementer of the same decision.

## Phase 3 - Complete Contract

Every handoff must include:

- `source_agent`
- `target_agent`
- `slice_id`
- `input_artifacts`
- `output_artifacts`
- `assumptions`
- `known_risks`
- `blockers`
- `validation_status`
- `next_action`

## Phase 4 - Classify Status

Use only statuses from `status-model.md`.

Do not move to `READY_FOR_REVIEW` without output artifacts. Do not move to `APPROVED` without reviewer evidence. Do not move to `DONE` without required validation or documented not-applicable status.

## Phase 5 - Classify Blockers

Use only:

- `REQUIRES_INPUT`
- `REQUIRES_DECISION`
- `REQUIRES_FIX`
- `REQUIRES_ARCHITECTURE_DECISION`

Every blocker must name its owner and required resolution.

## Phase 6 - Record Handoff

Use `templates/handoff-report-template.md` for reports.

Store handoff summaries in the workflow-designated report, matrix or slice quality log. Do not create hidden handoff state.
