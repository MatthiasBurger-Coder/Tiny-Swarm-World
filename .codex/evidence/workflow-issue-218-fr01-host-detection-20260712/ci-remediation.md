# FR-1 GitHub CI Remediation

Date: `2026-07-12`
PR: `#220`
Failed workflow run: `29200070600`
Failed job: `86669785903` — `Python Quality And SonarCloud`
Typed error classification: `QUALITY_FAILURE / BOOTSTRAP_IMPORT_COUPLING`
Live infrastructure: `NOT_RUN`

## Failure

The GitHub quality step stopped before Sonar analysis. Full discovery reported
21 failures and 1 error in installer-script tests. Every relevant traceback
ended in `ModuleNotFoundError: No module named 'pydantic'` while importing
`tiny_swarm_world.installer` before its dependency-bootstrap phase.

## Root cause

FR-1 initially located the standard-library host model under the existing
`domain.preflight` package. Python executes that package's eager `__init__`
before loading the submodule, transitively importing deployment models that
require `pydantic`. The installer intentionally starts before those third-party
dependencies are guaranteed. Its minimal temporary-checkout fixture also copied
only `installer.py`, so it did not represent the new explicit import closure.

## Focused correction

- Move `host_environment.py` and its evidence sanitizer to side-effect-free,
  standard-library-only modules directly under `domain`.
- Keep the existing `domain.preflight` public exports as compatibility aliases;
  no second classifier or DTO is introduced.
- Point the installer, detector port/use case, adapters, entry point, and legacy
  consumers at the side-effect-free domain module where applicable.
- Make the install-script fixture copy exactly the 15 standard-library files in
  the pre-bootstrap import closure, excluding caches and unrelated modules.
- Amend workflow scope, context hashes, arc42, and evidence for the observed
  bootstrap constraint.

## Verification after correction

- `PYTHONPATH=src python3 -S -c 'import tiny_swarm_world.installer'`: `PASS`.
- Deterministic compatibility subset: `PASS`, 42 tests in 8.650 seconds,
  including 23 install-script tests, the `-S` import guard, and legacy export
  identity.
- Expanded focused suite: `PASS`, 345 tests in 15.390 seconds.
- Expanded focused suite with `CI=1`: `PASS`, 345 tests in 15.214 seconds.
- Ruff: `PASS`.
- Mypy: `PASS`, 488 source files.
- Import Linter: `PASS`, 3 contracts, 300 files/687 dependencies.
- Hexagonal architecture tests: `PASS`, 18 tests.
- Final full quality gate: `PASS`, 1,456 tests in 94.715 seconds with
  28 expected skips; total gate time 128.2 seconds.
- `git diff --check`: `PASS` after final evidence consolidation.

The correction executes no live command and does not broaden FR-1 behavior.
GitHub CI/Sonar must rerun on the remediation commit before merge.

## Independent remediation reviews

- Senior System Architect: `PASS`; no open architecture, bootstrap, scope, or
  compatibility finding. The root-domain modules remain hexagonal and
  standard-library-only, legacy module paths preserve identity, and all current
  paths match the 50 allowed scope entries.
- Senior Tester / CI Reviewer: `PASS_FOR_CI_RERUN`; the root cause is covered,
  the 15-module closure and `-S` guard are deterministic, and no assertion was
  weakened. Independent affected-test, install-suite, focus, CI-focus, and full
  gate checks passed.
- Post-remediation Issue Completion Auditor:
  `PASS_FOR_CI_RERUN_PENDING_RELEASE`; 69 branch/worktree files are covered by
  all 50 allowed patterns, all 141 requirement IDs remain unique, all six
  required issue-evidence files are consistent, and no local FR-1 finding
  remains open.

The remediation may now be committed and pushed. GitHub Python 3.12, configured
Sonar, mergeability, merge, cleanup, and merged-main verification remain
mandatory release gates.
