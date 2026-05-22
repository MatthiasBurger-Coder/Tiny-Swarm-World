# Handoff Contract

## Required Fields

| Field | Meaning |
| --- | --- |
| `source_agent` | Current owner role or callable subagent. |
| `target_agent` | Next owner role or callable subagent. |
| `slice_id` | Stable workflow slice identifier. |
| `input_artifacts` | Files, reports, diffs, logs or decisions the target must read. |
| `output_artifacts` | Files, reports, diffs, logs or decisions the target must produce. |
| `assumptions` | Explicit assumptions accepted for this handoff. |
| `known_risks` | Risks that remain after source work. |
| `blockers` | Classified blockers and owners. |
| `validation_status` | Validation already run, pending or not applicable. |
| `next_action` | The next concrete action expected from the target. |

## Validation Rules

- All file paths must be repository-relative unless an absolute path is needed for tool output.
- Assumptions must include acceptance source or be treated as blockers.
- Blockers must use the status model in `workflow.md`.
- Validation status must name exact commands when commands were run.
- Handoffs involving changed files must include write ownership and merge order.

## Invalid Handoffs

A handoff is invalid when:

- any required field is empty;
- source or target cannot be verified;
- expected output is vague;
- blockers are listed without owner;
- validation status says clean without command evidence;
- a handoff asks two write-capable agents to edit the same file in parallel.
