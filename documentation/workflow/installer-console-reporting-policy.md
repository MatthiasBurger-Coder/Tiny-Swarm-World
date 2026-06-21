# Installer Console Reporting Policy Workflow

## Scope

Define and enforce human-readable installer console reporting for `install.sh`
and `python3 -m tiny_swarm_world.installer`.

## Non-Goals

Do not implement an interactive console GUI, curses interface, menu controller,
or behavior-changing provisioning shortcut. Do not remove JSON report files,
Markdown reports, logs, or evidence generation.

## Branch Rule

Policy work uses an architecture branch. Implementation and guard work use
feature branches. Combined remediation branches must still avoid direct changes
on `main`, `master`, or `develop`.

## Architecture Rule

Installer state belongs to the application layer. Console rendering is an
infrastructure adapter behind a reporting port. Domain event models do not print
and do not depend on JSON serialization or terminal libraries.

## Output Policy

Valid console output is stable, line-oriented, and readable:

```text
[1/2] fresh-install reset
  RUNNING fresh-install reset started
  OK      fresh-install reset completed
```

Invalid console output includes raw structured payloads:

```text
{"step":"preflight","status":"success"}
{'step': 'preflight', 'status': 'success'}
InstallEvent(step='preflight')
!!python/object
```

Raw JSON, raw Python dictionaries, YAML payloads, internal event object
representations, and unformatted stack traces must not appear on stdout or
stderr during normal installer operation. JSON is allowed only as a generated
report file.

## Acceptance Criteria

- Normal and verbose output are human-readable.
- CI output, when present, is line-based text and not JSON.
- Failed steps include target, reason, evidence path, and suggested checks when available.
- Reporters render events; they do not execute diagnostic commands.
- Automated tests fail on raw JSON, dict, YAML, or event repr output.

## Quality Gates

Run targeted reporter tests first, then `python3 tools/quality_gate.py quality`
when practical. Do not execute live infrastructure commands for these checks.

## Handoff

Follow-up implementation work owns additional phase mappings, optional report
files under ignored report directories, and live-run evidence integration.
