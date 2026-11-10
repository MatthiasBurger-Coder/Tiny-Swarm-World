# Exact-source qualification and operator-path contract

## Public commands verified in source/tests

These are command templates for later admitted scenarios, not operations run by
workflow create. Execute project Python/CLI through the designated SSH/WSL session
and verify the installed candidate package/root. Native deployments are distinct
targets; carry their own admitted identities and before/after evidence.

```bash
tiny-swarm-world product version
tiny-swarm-world product upgrade --to 0.5.0 --preview
tiny-swarm-world services list
tiny-swarm-world services updates
tiny-swarm-world services update --services portainer --to portainer-ce-2.45.1 --preview
tiny-swarm-world services update --services swagger --preview
tiny-swarm-world services update --services swagger,traefik --preview
tiny-swarm-world setup run --minimal --preview
tiny-swarm-world setup run --services swagger --preview
tiny-swarm-world setup run --services swagger,traefik --preview
tiny-swarm-world services add --services swagger --preview
tiny-swarm-world services remove --services swagger --preview
```

Live apply/recovery uses the corresponding already implemented --live,
--approve-live and --recover contracts only after exact scenario consent, JIT and
backup/ownership admission. Read-only preview is never called live verification.
S440-01 must verify each actual installed help/argument contract and map command
tokens to __main__/CLI → service → port → adapter → persisted/effect state.
Legacy platform update/recover remains compatible. Do not use the provisional
one-token version/update spellings from the parent issue as shipped commands.

## Source freeze and evidence contract

Per scenario record run ID, source commit/archive and relevant file hashes,
installed package/launcher identity, exact command/argv (redacted), timestamps,
process identity and exit, host/OS/WSL/Incus client/server versions, profile,
persisted resolved selection, intended images and actual service/task digests,
route/device/consumer tuples, authenticated service/data/ownership facts,
checkpoint/signal correspondence and retained final state. Store raw evidence
privately; publish only redacted summaries and content checksums.

Use immutable image platform/config identities; tag, index and child digest are
distinct. Re-resolve availability rather than assuming the historical proposal
is still present. Data/credential preservation uses protected in-memory/private
comparisons, never printed values or credential-derived public hashes.

## Qualification/admission sequencing

1. Scoped profile code and deterministic tests may precede fixture success under accepted R67k; all runtime version admission stays empty/fail-closed.
2. The isolated listener fixture is separately reviewed/authorized and qualifies exact Incus behavior. It does not run product operations or modify customer routes.
3. Independent evidence review permits a separate exact capability-asset admission; unknown versions remain denied. Subsequent setup/upgrade still needs its own scenario GO.
4. For component transitions, the main catalog stays candidate-only until qualification. S440-01/05 must specify an independently reviewed proposed policy on a private, isolated qualification candidate branch/worktree. Its source includes the proposed exact policy and runs through the unchanged public admission/executor against owned recoverable fixtures. This is qualification of a code candidate, not an already supported release. No live monkeypatch, direct-adapter bypass, general force flag or production catalog rewrite is permitted.
5. Record the candidate policy delta, exact tested source and permitted target/scenario in the GO. Only after successful attributable single/batch/recovery results and independent acceptance may that exact policy candidate be consolidated as supported. Failed candidates stay unadmitted. If the guarded public-path sequence cannot be established without weakening policy, stop S440-09 for reviewed contract refinement.
6. Live evidence remains bound to its original source. Later runtime/config/asset changes invalidate affected cases. Evidence-only changes need an explicit independent equivalence decision; do not demand a self-referential report hash or silently call a changed final commit live-tested.

## Mandatory live cases

| Group | Cases and exact required observations |
|---|---|
| Incus | Each claimed host, exact 6.0.5 client/server, owned isolated loopback port, no listener before start, attributable loopback HTTP after start, no wildcard/customer-route change, verified cleanup and unchanged foreign consumers/Windows rules |
| Portainer | Existing TSW-selected Portainer-managed stack; real cold /data backup; 2.45.0→2.45.1 Server/Agent; auth/admin/endpoint/data/stack identity; managed update and converged tasks; repeat no-op; process-bound interruption, API-down cold recovery and repeat recovery |
| Components | Exact supported source bundle; Swagger single and Swagger+Traefik batch with both changed; full task-image convergence and auth; desired pins persisted; later ordinary setup retains targets; no-op; partial batch/interruption/resume/recovery; old/mixed tasks and drift refusal |
| Selection | Fresh minimal; Swagger optional and Swagger+Traefik optional where actually distinct after dependency resolution; add to existing installation; preserve IDs/data/credentials/overrides; only selected routes/output/checks; omitted services not falsely failed; explicit preview-only removal |
| Product/shared | Preserve accepted historical official 0.4.0→0.5.0; map missing current manifest-v2/scoped variants; dirty/unofficial/moved-source meaning, invalid targets/downgrades, refused consent/invalid input, missing/stale checkpoints, mixed tasks and applicable drift; supported recover/no-op with real signal/checkpoint attribution |

Native and WSL results remain separate for every claimed scenario. If proposed
optional requests resolve to the same service set, select another actually
supported distinct set before claiming two selections. Existing full-service
installation/browser passes do not fill missing update/selection cells.

## Listener/helper binding prerequisite

The current fixture reads HEAD:documentation/handbook/05-development/workflow/issues/issue-449/workflow.md.
The previous source is preserved in Git at the workflow baseline; the active tree
is regenerated. Do not attempt a GO under an old path/hash or create a dummy
compatibility document to bypass approval. S440-05 must implement/review the
active-workflow binding and tests, verify all capture/maintenance consumers and
freeze the new approval schema/hash. Existing expected-approval-sha256 and target
identity checks remain mandatory. New harness commands become executable only
after their implementation/help/tests are accepted and the plan is refreshed.

## S440-01 inspected executable and effect ownership

| Delivered entrypoint | Actual production path and authority |
|---|---|
| Root tsw | modules/tsw_native_linux/tsw → boostrap/run.sh → python3 -m modules.tsw_core.src → core __main__ → CLI dispatcher |
| Installed tiny-swarm-world | pyproject console script → tiny_swarm_world.__main__:cli → dispatcher.main/parser.parse_args; verify installed package is the campaign source |
| product version / services list | lifecycle.run_lifecycle_inspection → composed InstallationLifecycleService.inspect; persisted catalog/manifest observations, not a fresh runtime claim |
| product upgrade | ProductUpgradeService + PreparedProductInstallation/OfficialProductSource/JsonProductJournal + ClassicProductRuntime; protected code/env/config staging and full-selection verification |
| services updates/update | ComponentUpdateService → domain admission → ComponentUpdateExecution → Classic/ManagedComponentRuntime → #297/Portainer; desired pins only after observed success |
| Portainer-only update | Dedicated preview/consent/no-batch guard → PortainerUpgradeService → ClassicPortainerUpgradeRuntime and JsonPortainerJournal; cold backup/manager-shell restore and managed-stack identity |
| setup/add | Selection planner → installation lease → SetupSelectionState.admit → scoped preparation/existing SetupWorkflow → observations and manifest commitment |
| removal/selection preview | Pure persisted plan and route projection; removal apply unsupported |
| scoped runtime/recovery | ProfileRuntimeOperation and InstallationProfileService invoke JSON capability authority and checkpoint/lease-bound runtime; exact devices/consumers/client/server rechecked before effects |

The runtime support authority is the reviewed JSON capability asset, currently
empty, not the separate unsupported data-only intent classifier. Old workflow
binding remains a genuine S440-05 prerequisite. No caller bypass or production
candidate promotion was performed during this inventory.

### Current deterministic verification

The five CLI suites in S440-01 ran on the isolated designated SSH/WSL test source:
96 tests PASS, zero skips. Initial retry was BUILD_FAILURE (DevOps, retry 1/3):
the new test log directory had 0755 instead of required owner-private 0700.
Corrected only the newly owned test-state directories; no application guard,
test assertion or live installation was changed. Retry command was the same
five-suite PYTHONPATH=. python3 -m unittest command in slice metadata.

These tests substitute host/runtime effects and prove CLI contracts only.
No live fixture, backup, service update or native/WSL system acceptance follows.
