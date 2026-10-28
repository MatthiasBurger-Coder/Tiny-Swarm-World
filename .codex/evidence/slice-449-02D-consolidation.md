# S449-02D consolidation evidence

## Scope and disposition

- Workflow: `issue-449-lcm-w09`, v1.33.
- Slice: `S449-02D — Isolate the disposable fixture from shared default routes`.
- Source baseline commit: `2ff894d0a687683fdfbef46a191b4b9ad5550d61`.
- Execution was serialized in one Python/test stream because the fixture runner and its regression suite share file and lifecycle locks.
- No host inventory, Incus fixture, install, upgrade, service, firewall, or routing command was executed in this slice. No host mutation occurred.

## Implemented changes

- The disposable fixture uses allowlisted derived base-profile data, forces `boot.autostart` to the Incus string `false`, and never attaches or mutates the shared `default` profile.
- Source profile identity, complete canonical digest, and sorted `used_by` consumers are checked at each write boundary.
- Fixture profile cleanup recognizes only exact owned prefixes, including an ambiguous marker-only profile after a partial write.
- Cleanup verifies ownership and continues removing owned resources after route drift; every cleanup write and cleanup completion rechecks the full profile, listener, all-project route, WSL rule/PortProxy snapshot, and approved route digest.
- Inventory capture and cleanup have bounded command, byte, entity, and elapsed-time budgets, with reserved cleanup capacity.
- Deterministic regression coverage exercises malformed profile data, collisions, partial and ambiguous create outcomes, pre-write drift, post-delete route drift, cleanup order, and the reserved budgets.

## Exact source and verification

The current local files were copied to the approved PC WSL checkout `/home/pc/projects/issue449-s449-02-509908`; the WSL SHA-256 values matched the local values before verification:

| File | SHA-256 |
|---|---|
| `tools/qualification/incus_profile_listener_fixture.py` | `4d1bef40aa2be3f3f477d33c98db173bf43290cf23a71f33f9937e0fd089221f` |
| `tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py` | `deb5a79c706b8f277df55e36e040e2ca0c33289a4b7b1debe58a7f260822b1bc` |

- `git diff --check`: PASS.
- Focused test on PC WSL with Python 3.12: `PYTHONPATH=src ~/.local/bin/python3.12 -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture` — PASS, 102 tests.
- Full required quality gate on PC WSL: `XDG_STATE_HOME=/tmp/tsw449-quality-state-final-20261028 /tmp/tsw449-quality-venv/bin/python tools/quality_gate.py quality` — PASS. All gates completed, including verification-policy, complexity, lint, import-linter, architecture tests, typecheck, and the full suite (`2976` tests, `18` skipped).
- The initial focused run exposed two test-fixture issues introduced by the stronger cleanup checkpoint; these were corrected. The final focused and full gates above passed on the corrected hashes.

## Independent reviews

- Requirement review: APPROVED; previous consumer-drift and partial marker-only cleanup findings are closed. The full route/profile checkpoint is enforced at cleanup writes and completion.
- Architecture review: APPROVED; the fixture remains a standalone qualification runner within the declared allowed files, with no application/domain boundary changes.
- Security review: APPROVED; inventory commands and outputs remain bounded, persisted command records omit raw arguments/output, and cleanup remains run-name scoped with ownership readback.
- Quality review: APPROVED; cleanup budget reserves are consistent and tested.
- S3D: `EXECUTION_PLAN` for S449-02D only; serial Python/test stream. It authorizes no later slice, host action, or live scenario.
- No role-based fallback was needed; real subagents were used. This consolidation is the root integration decision.

## Remaining status

S449-02D is implementation-complete and locally verified. This does not qualify either host and does not complete issue #449. S449-02E is the next dependent slice and requires its own fresh approvals and S3D plan. Existing native Incus ownership/service and WSL route/feature blockers remain for later workflow slices. No per-host admission or scenario GO is established by this evidence.
