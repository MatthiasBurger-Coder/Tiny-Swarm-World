# Quality Results

Workflow ID: `workflow-sonar-s5527-tls-20260623`
Date: `2026-06-23`

## Commands

### Static Sonar Rule Check

Command:

```bash
rg -n "_create_unverified_context|ssl\.create_default_context" src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py tests/infrastructure/adapters/preflight/test_host_preflight_probe.py
```

Result: passed.

Evidence:

- No `_create_unverified_context` occurrence remains in the target file.
- Remaining TLS context creation is
  `ssl.create_default_context()` in
  `src/tiny_swarm_world/infrastructure/adapters/preflight/host_preflight_probe.py`.

### Focused Unit Test

Command:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_host_preflight_probe
```

Result: passed.

Evidence:

- Ran 34 tests.
- Result: `OK`.

### Quality Gate Test Subgate

Command:

```bash
python3 tools/quality_gate.py test
```

Result: passed.

Evidence:

- Ran 954 tests.
- Skipped 19 tests.
- Result: `OK`.

### Diff Whitespace Check

Command:

```bash
git diff --check
```

Result: passed.

Evidence:

- No whitespace errors reported.

## Full Quality Gate

`python3 tools/quality_gate.py quality` was not run because the requested
minimum was targeted checks plus the relevant quality-gate test subgate, and
the focused change is covered by the preflight unit test plus repository test
subgate. No full quality pass is claimed.

## Live Infrastructure Safety

No live infrastructure commands were executed.
