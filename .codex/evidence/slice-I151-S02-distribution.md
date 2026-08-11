# I151-S02 Distribution and Handoff

Slice: Deterministic summary formatter

Owner role: Console/status UI Developer

Secondary review roles: Senior Python Automation Developer, Senior Tester,
Senior System Architect

Execution mode: explicit role-based fallback in the main thread. Shared output
contracts make parallel execution unsafe.

## Implemented contract

- Workflow summaries are projected to stable line tuples before printing.
- Setup summaries expose workflow, phase count, status counts, phase-group
  status/limit/duration, individual phase status, message, reason, and final
  status.
- Verification summaries expose deterministic status counts and sorted evidence
  keys.
- Mapping/list/structured evidence values are represented as a persistence hint,
  not as a raw object dump. Scalar evidence paths and operator-facing values
  remain visible.
- The explicit JSON branch still serializes the original structured result.

## Verification

```text
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint
```

Result: `PASS` — 60 tests.

## Handoff

S03 may route the installer/default paths through this formatter contract while
preserving exit codes, logs, and evidence directories.
