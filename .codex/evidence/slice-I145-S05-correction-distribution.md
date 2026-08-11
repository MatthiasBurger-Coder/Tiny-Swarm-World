# S05 Evidence Contract Correction — I145-S05

Primary role: Senior Python Automation Developer
Review roles: Senior Tester, Issue Completion Auditor

`SetupPhaseGroupResult` now includes stable `phase_ids`, `phase_names`,
`started_at`, `finished_at`, `duration_seconds`, status and the configured
limit. This closes the original issue's operator-evidence requirement without
changing the asyncio scheduling or safety boundaries.

Verification:

```text
PYTHONPATH=src python3 -m unittest tests.application.services.setup.test_setup_workflow
Ran 33 tests in 2.038s
OK
```

The full quality gate was rerun after this correction and remains green.
