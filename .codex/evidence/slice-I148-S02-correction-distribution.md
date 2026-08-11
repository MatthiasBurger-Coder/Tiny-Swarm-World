# S02 Correction Review — I148-S02

Primary role: Senior Python Automation Developer
Review roles: Senior Tester, Issue Completion Auditor

The audit found that later bootstrap helpers can append exports after the
initial parse. The snapshot now receives those appended values through
`_snapshot_with_exports()`, and keys that were already present are marked as
duplicates before normalization. This prevents generated or policy/default
values from being lost when duplicate cleanup runs.

Verification:

```text
PYTHONPATH=src python3 -m unittest tests.test_installer
Ran 42 tests in 0.280s
OK
```

The new regression test covers replacement plus duplicate tracking. The full
quality gate was rerun after this correction and remains green.
