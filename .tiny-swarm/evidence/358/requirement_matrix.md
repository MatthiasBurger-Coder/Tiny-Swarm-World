# Issue #358 requirement matrix

| ID | Requirement | Type | Likely files | Implementation evidence | Verification evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Move workflow semantics out of CLI modules so CLI code has no substantial infrastructure orchestration. | Architecture | `src/tiny_swarm_world/__main__.py`, application services, composition | `composition_cli.py`, `cli_dispatch.py`, `prepare_with_preflight.py` | `arch-lint`, `arch-tests`, CLI tests | VERIFIED |
| REQ-002 | Isolate command parsing and routing from workflow semantics. | Architecture | CLI entrypoint, application services | `__main__.py` delegates to `execute_cli_workflow` | CLI tests, static diff | VERIFIED |
| REQ-003 | Keep presentation separate from workflow semantics. | Architecture | CLI entrypoint, presentation module | `cli_presentation.py`, `setup/installation_plan.py` | CLI formatting and setup plan tests | VERIFIED |
| REQ-004 | Invoke application behavior through explicit use cases or services. | Behavior | application services, composition, CLI entrypoint | `cli_dispatch.py`, `PrepareHostWithPreflight`, existing workflow services | CLI tests, host use-case tests | VERIFIED |
| REQ-005 | Preserve supported command names and options. | Compatibility | CLI parser and tests | CLI registry and parser unchanged | Frozen 19-command tuple in `test_every_declared_workflow_keeps_its_command_name`; CLI tests | VERIFIED |
| REQ-006 | Preserve live consent and destructive confirmation safeguards. | Safety | CLI routing and tests | `_live_consent_for_workflow`, `_enforce_workflow_confirmation` retained | Existing CLI consent and confirmation tests | VERIFIED |
| REQ-007 | Preserve command exit semantics. | Compatibility | CLI routing and tests | Exit mapping retained in `__main__.py` | Existing CLI exit tests | VERIFIED |
| REQ-008 | Cover supported commands and exit behavior with CLI regression tests. | Test | `tests/test_package_entrypoint.py`, related tests | Frozen registry, all mutating commands' exit-2 consent test, existing success/failure exit tests | Targeted CLI test suite | VERIFIED |
| REQ-009 | Update relevant architecture documentation and issue evidence. | Documentation | `documentation/arc42`, `.tiny-swarm/evidence/358` | C-011 architecture row and this evidence package | `git diff --check`, evidence audit | VERIFIED |
