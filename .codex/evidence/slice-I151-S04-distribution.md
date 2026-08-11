# I151-S04 Distribution and Handoff

Slice: Preserve explicit debug/machine-readable JSON

Owner role: Senior Python Automation Developer

Secondary review roles: Console/status UI Developer, Senior Tester

Execution mode: explicit role-based fallback. The JSON opt-in contract was
verified against the already-separated normal formatter path.

## Verification

- `--json` remains the explicit structured CLI output mode.
- `TSW_DEBUG_JSON=true` enables structured output without changing the parser
  default.
- `TSW_DEBUG_JSON=false` keeps the normal line-based summary.
- Setup result `to_dict()` continues to preserve phase/group data for structured
  consumers; installer evidence/log persistence is unchanged.

```text
PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.application.services.setup.test_setup_workflow
```

Result: `PASS` — 95 tests.
