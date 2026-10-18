# Test results — issue #445

Baseline SHA: `3200347bfb203a79ad9373872e6da58c8a4e775a` plus the uncommitted
issue branch changes. Source fingerprints are in source_hashes.json.
Host: WSL2 Linux 6.18.33.2; Python 3.14.4; Classic policy fixtures for native-linux
and wsl2. Version identities in successful upgrade tests are synthetic catalog
policy, never evidence of an actual supported release or live transition.

Command (exit 0; 40 tests PASS):

```bash
PYTHONPATH=src python3 -m unittest tests.domain.lifecycle.test_update_planning tests.application.services.test_component_updates tests.test_component_updates_cli tests.test_lifecycle_cli tests.test_service_selection_cli tests.infrastructure.adapters.lifecycle.test_catalog tests.application.services.test_lifecycle
```

Read-only tests compare all installation-directory file bytes and modification
times before/after CLI/service calls, assert no manifest save, no subprocess,
no logger/runtime path setup, and inspect exact plan/discovery results.

Required full command: `tools/quality_gate.py quality`.

Verification source: detached baseline worktree `/tmp/issue-445-verification`
overlaid with the complete task changes, SHA256 matched to the original checkout.
The final 17-file implementation/test/doc/registry snapshot is recorded in
`source_hashes.json` (reviewable copy: `issue-445-source-hashes.json`).

```bash
cd /tmp/issue-445-verification
PATH=/tmp/issue-445-py312/bin:$PATH /tmp/issue-445-py312/bin/python tools/quality_gate.py quality
```

First complete Python 3.12 gate: all pre-test gates passed; 2747 tests ran in
207.559 seconds, one failure and 18 opt-in skips. The failure was the README
hash cached in skill-registry.json after this issue's README update. Refreshed
only that hash; the registry integrity test verifies it without changing tests
or governance behavior. Final complete gate after this refresh: PASS (exit 0).
All stages passed: verification-policy, complexity, lint, arch-lint (7 contracts),
arch-tests (43 tests), typecheck (845 source files), test (2747 tests in
175.752 seconds, 18 existing opt-in skips). Skips are not passes or live evidence.
The complete successful output is retained at `quality_python312.log` in the
local issue evidence directory (original: `/tmp/issue-445-quality-pass.log`).
The targeted registry integrity suite also passed: 5 tests, exit 0.

Two earlier Python 3.14 runs on the Windows mount were aborted (SIGTERM/exit241)
after source edits or severe filesystem stalls. They are NON-PASS/INDETERMINATE;
result markers were present without final tracebacks, so no individual failure
classification or success is claimed for those incomplete runs. The complete
supported-Python run above supplied the actionable cache failure. No tests were
skipped to work around the stalls; the native Linux worktree preserves test scope.
Continuation verification: the 40 targeted tests passed again in 3.199 seconds;
all 5 registry checks passed in 1.163 seconds. The additional Python 3.14 full
rerun (`/tmp/issue-445-quality-resume.log`) passed policy/complexity/lint,
7 architecture contracts, 43 architecture tests and type checking (845 files).
Its test phase did not produce a final result and was terminated with SIGTERM
(exit 241) after no further progress was observed. It remains INDETERMINATE,
never PASS. The supported Python 3.12 complete gate remains the acceptance
result. No tests or rules were removed to obtain that result.

Additional compatibility command (exit 0; 19 tests PASS on Python 3.12.14):

```bash
python3.12 -m venv /tmp/issue-445-py312
/tmp/issue-445-py312/bin/python -m pip install --require-hashes -r requirements.lock
PYTHONPATH=src /tmp/issue-445-py312/bin/python -m unittest tests.domain.lifecycle.test_update_planning tests.application.services.test_component_updates tests.test_component_updates_cli
```

The bare Python 3.12 interpreter initially lacked pydantic; the isolated locked
runtime resolved that environment prerequisite. No repository dependency changes.
The explicit registry command-name regression test was updated to include the
new read-only commands and its focused run passed (exit 0; one test).

Initial development lint/type failures and test fixture assumptions were repaired
in scope; no gate/threshold was weakened. Independent architecture reviewer
re-ran domain/application tests: 14 PASS.

Local checks: APPLICABLE_LOCAL. Installation, service, browser and host upgrade
qualification: NOT_APPLICABLE / LIVE_NOT_APPLICABLE to this read-only code slice;
W09 owns live qualification. SonarQube: EXTERNAL_GATE_NOT_APPLICABLE to local
completion; no external success claim. No infrastructure commands were executed.
