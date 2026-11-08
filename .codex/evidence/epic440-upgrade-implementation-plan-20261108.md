# EPIC 440: bounded upgrade acceptance implementation proposal R2

Status: SOURCE DESIGN ONLY; amended Root-authorized proposal, not implemented or qualified.
R2 supersedes only the design artifact, retaining original06248068d3f746d1b16fe12f752800c7bea816b6169247ea7972e12d4628cecf unchanged.
Root accepted the independent budget/scope findings and requested these exact
coverage, ledger, parser, recovery-purpose and legacy pre-launch corrections.
Prepared 2026-11-08 by requirements reviewer. Inspected checkout HEAD
`30d91f6472e2ff25583733ca660ff013fd0b9293`; later freezes must name their actual revision.
No project tests, hosts, infrastructure effects, product edits, or commits performed.

## Verified delivery boundaries

- `preserving_product_acceptance.RECIPES` and the WSL runner implement eight
  fresh/add cases. Their success is not update/upgrade acceptance.
- `component_transitions.with_stack_transition` contains genuine immutable full
  Swagger/Traefik bundles, but marks both targets `candidate-transition`.
  `update_planning` and `ComponentUpdateExecution._admit` refuse them, including
  forward resume after qualification is withdrawn. Do not bypass either guard.
- `setup_state._effective_inventory` / `desired_images.effective_component_inventory`
  consume image overrides; `SetupComponentObservations` verifies complete pinned
  Swagger/Traefik source bundles against actual desired/task images before commit.
- Compose Portainer defaults are already 2.45.1. A normal fresh setup tests only
  the upgrade no-op branch. Dedicated upgrade source/target are 2.45.0/2.45.1.
  `ClassicPortainerUpgradeRuntime` verifies cold backup, original identities,
  endpoints/ownership, actual image convergence, saved-stack reapply and tasks.
- `PortainerUpgradeService` requires an actual optional Portainer-managed stack;
  upgrade recovery of a settled success is intentionally refused. Recovery tests
  need a genuinely interrupted operation, not a completed upgrade downgrade.
- `product-releases.json` pins official 0.4.0
  `346f4a43dbdc43380e7bc703ab185bc06746965b` to 0.5.0
  `b3de7fa16e24c5702d61f855851c6c3255871489`. Both immutable readers support ONLY
  schema 1, both package metadata versions are 0.2.0. Product admission requires
  Python 3.12, exact official source/ref/lock, clean checkout and resource checks.
  Product upgrade preserves component images; it does not upgrade Portainer.
- Published 0.4.0 has full `setup run`, Incus backend selection, but no selective
  services/adoption commands or scoped creation journals. Its provider launches
  nodes directly. Neither current Schema-2 manifests nor fabricated profile
  checkpoints/markers can supply a real legacy source installation.
- Current `owned_case_disposal.DisposalIntent` requires authentic scoped creation
  checkpoints, generated profile names and installation/operation markers.
  KEEP that contract unchanged for scoped cases. It cannot clean legacy nodes.
- WSL finish/GuestSwitch currently bind a schema-1 ledger of at most eight closed
  cases. New upgrade cases require an explicit producer/consumer ledger revision;
  silently omitting their children/outcomes from ReturnOriginal is unsafe.

## Authorization requested: two ordered source slices

S-U1: actual scoped component/Portainer acceptance, then S-U2: official legacy
product acceptance. Root retains integration, gates, live GO and publication.
Specialists may implement source/tests in isolated worktrees only after Root
records these locks. No infrastructure authority follows from source approval.

Exact common allowed files, new unless noted:

1. `tools/linux/qualification/product_upgrade_cases.py`: fixed recipe table,
   orchestration/proof helpers and finite phase-aware child supervision.
2. `tests/tools/test_product_upgrade_cases.py`: real orchestration with fake
   transport/process/filesystem boundaries; no replacement of lifecycle engines.
3. `tools/linux/qualification/preserving_product_acceptance.py` (existing):
   dispatch closed upgrade cases; source pins; phase-specific fixed baseline env;
   supervised public child and ledger integration; retain existing eight recipes.
4. `tests/tools/test_preserving_product_acceptance.py` (existing).
5. `tools/linux/qualification/wsl_product_acceptance.py` (existing): same dispatch,
   source/identity/config checks, deadlines and ledger producer integration.
6. `tests/tools/test_wsl_product_acceptance.py` (existing).
7. `tools/windows/qualification/wsl_acceptance_guest_switch.ps1` (existing): ONLY
   strict new ledger-version/closed-case parsing and recognition of the new fixed
   qualification child path; no reset, registry, bridge or preservation weakening.
8. `tests/fixtures/wsl_acceptance_guest_switch.ps1` (existing): ledger fixtures.
9. `tests/tools/test_wsl_acceptance_guest_switch.py` (existing): reject omitted,
   duplicate, unknown, unsettled and wrong-source upgrade outcomes.
10. `.codex/evidence/epic440-upgrade-acceptance-20261108.md`: source/evidence record.

S-U1 additionally locks exactly
`src/tiny_swarm_world/infrastructure/adapters/lifecycle/component_transitions.py`,
`tests/infrastructure/adapters/lifecycle/test_native_component_transitions.py`
and `tests/application/services/test_component_updates.py` (all existing).
Its production delta is the explicit two-target qualification status described
below, not a new escape hatch. No runtime/domain guard modification authorized.
Keep a real explicit candidate-policy rejection test by demoting only the test
input; test accepted native policies directly without the current test helper's
synthetic promotion. These unit data arrangements never authorize live dispatch.

S-U2 additionally locks exactly
`tools/linux/qualification/legacy_product_baseline.py` and
`tests/tools/test_legacy_product_baseline.py`. Keep legacy ownership/disposal
inside that helper instead of broadening `owned_case_disposal` to accept missing
markers. If an actual released-CLI incompatibility or production failure occurs,
report it before requesting any additional product file lock.

Root alone updates workflow/ADR authority for new budgets, ledger ABI and legacy
profile mutations before live use. Bridge source/registration and native
maintenance/provenance modules are outside these authoring locks.

## Genuine catalog qualification, without synthetic admission

1. Freeze an unpublished, reviewed qualification candidate revision containing
   the actual NativeComponentCatalog and unchanged exact transition policies,
   with ONLY the two literal status values set to `qualified-transition`.
   Its release/publication status remains UNQUALIFIED; authoring a status value
   supplies executable test input, not a compatibility PASS claim.
2. Execute the public CLI from that exact private clean candidate checkout on
   fixture-owned installations. No alternate catalog, monkeypatch, environment
   qualification switch, target expansion, fabricated runtime observation or
   acceptance-policy shortcut is allowed.
3. Bind both hosts' actual case artifacts to full source revision, executing
   file pins, immutable source/target bundles and host identity. Require all
   scoped upgrade cases below and persistence/recovery evidence before public
   promotion. Negative unqualified/unsupported/downgrade cases remain covered.
4. Publish the SAME tested source revision only after independent evidence review.
   Keep acceptance evidence/promotion records separate from tested executing bytes
   so recording PASS cannot silently change the qualified implementation. Any
   relevant source change requires new applicability review and reruns as needed.
5. Before those actual results exist, normal distributed/current source stays
   candidate-only. Never present a private candidate as released compatibility.

## Closed cases (each on native .33 and same-PC WSL .58)

Append these SIXTEEN names after the existing eight in this exact fixed order.
Every case runs independently on BOTH native .33 and same-PC WSL .58. The eight
normal batch rows are the complete Cartesian product of both declared presets,
both optional writers and both stored Swagger exposures; BOTH immutable component
transitions run in EACH batch. The retained eight other cases do not substitute
for any batch tuple. Additional recovery variants are not claimed by this scope.

| Case | Real baseline | Exercise / required result |
| --- | --- | --- |
| upgrade-swagger-swarm | default; scoped Swagger, published, Swarm owner | UI 5.32.6→5.32.7; full four-member bundle verified; repeat no redeploy |
| upgrade-traefik-swarm | default; scoped Traefik, Swarm owner | 3.7.4→3.7.5; auth/TLS/routes; repeat no redeploy |
| upgrade-batch-default-swarm-published | default; Swagger+Traefik; Swarm; published | both transitions, full retained bundle/config/routes/IDs, actual repeat no-op, target-pin persistence |
| upgrade-batch-default-swarm-internal | default; Swagger+Traefik; Swarm; internal | both transitions; internal Swagger stays unpublished, only actual selected Traefik ingress remains |
| upgrade-batch-default-portainer-published | default; Swagger+Traefik; Portainer; published | both transitions through exact saved stack IDs/Env/ResourceControl, convergence and target-pin persistence |
| upgrade-batch-default-portainer-internal | default; Swagger+Traefik; Portainer; internal | both transitions; full saved definition and internal Swagger absence proof, repeat and persistence |
| upgrade-batch-service-access-swarm-published | service-access; Swagger+Traefik; Swarm; published | both transitions, full retained bundle/config/routes/IDs, actual repeat no-op, target-pin persistence |
| upgrade-batch-service-access-swarm-internal | service-access; Swagger+Traefik; Swarm; internal | both transitions; internal Swagger stays unpublished, only actual selected Traefik ingress remains |
| upgrade-batch-service-access-portainer-published | service-access; Swagger+Traefik; Portainer; published | both transitions through exact saved stack IDs/Env/ResourceControl, convergence and target-pin persistence |
| upgrade-batch-service-access-portainer-internal | service-access; Swagger+Traefik; Portainer; internal | both transitions; full saved definition and internal Swagger absence proof, repeat and persistence |
| recover-batch-swarm | default; fresh source-version batch, Swagger internal, Swarm owners | bounded interruption after real durable stage; original selection --recover; source pins/tasks restored; repeat recovery has no redeploy |
| recover-batch-portainer | default; fresh source-version batch, Swagger published, actual Portainer owners | same recovery with exact endpoint/stack authority; no direct-Swarm writer |
| upgrade-portainer | default; scoped Swagger optional Portainer owner; server+agent2.45.0 | cold backup→2.45.1; auth/data/endpoints/ownership; real managed-stack reapply+tasks; repeat no backup/update/reapply |
| recover-portainer | default; independent identical 2.45.0 fixture | real interruption with durable checked backup; --recover restores same /data/source images/IDs/credentials; repeat no-op |
| upgrade-product-v1 | service-access; actual official0.4.0 full legacy fixture | public0.5.0 preview/apply; target interpreter/runtime/active launcher; schema1 preserved; repeat verified no-op |
| recover-product-v1 | service-access; independent actual0.4.0 full fixture | real interrupted staging/switch/commit; management --recover finishes exact target; old source/runtime/data preserved; repeat no-op |

This is bounded minimum coverage, not a claim that every wider W09 criterion is
now satisfied. Compare the final workflow acceptance matrix explicitly; any
remaining destructive/corruption/negative/browser criteria stay separately open.
Normal batch coverage requires all16 actual host×preset×owner×exposure tuples,
not separate appearances of each dimension. Public promotion of both declared
presets/hosts is forbidden until EACH tuple has exact-source actual evidence and
independent acceptance. Fresh/add cases are complementary, not a transition
substitute. Failure/missing/NOT_EXERCISED tuples keep publication UNQUALIFIED.

## Shared interfaces and scope authority

`UpgradeRecipe`: frozen literal case/kind/preset/selection/exposure/owner/fault enum;
no arbitrary arguments, executable, URL, callbacks, destinations or timeouts.
`run_upgrade_case(port, recipe)` receives the already admitted case-private
port, actual installation root and immutable source/profile intent. Production
factory constructs only the existing Native/Wsl ports; mocks exist only in tests.

Narrow private operations: `public_fixed(step)` derives argv from the recipe;
`observe_upgrade()` authenticates through existing real observers;
`interrupt_owned_child(stage)` supervises only its own gated Popen process group;
`record_proof(stage, bounded_redacted_value)` writes private CAS/fsynced journals.
No context-wide authority, ambient lease, new public CLI flags or callable ports
from operator JSON. Retain all current source/config/identity JIT checks and
private operation leases, including re-admission before every writer.

Baseline image env is a literal recipe-owned layer, independent of operator
credentials: Swagger source full four-member digest bundle, Traefik source
digest, or Portainer source server+agent digests. Set it only for baseline
setup/artifact preparation. Remove source overrides before update/recovery so
they cannot conflict with the engine's admitted transition overrides. Operator
file retains its exact 16 credential-input allowlist; scope, TLS, selection,
source, image and evidence authority are applied last from the closed recipe.
Assert actual desired/task identities and source manifest before any update.
Never fill observed identities from desired/catalog values.

### Exact public preset binding

The actual current parser defines global `--service-profile` with exactly
`default`/`service-access`. Selective `setup run --services ...` accepts the
explicit flag; use `setup run --services swagger,traefik --service-profile
<literal recipe preset>` plus fixed owner/exposure and consent flags for EACH
batch baseline. Assert persisted manifest.service_preset and actual setup plan
match that literal BEFORE starting updates. No environment/default may stand in
for this binding. The immutable official0.4.0 parser also has this public flag;
its full legacy setup is explicitly bound to service-access.

IMPORTANT actual ABI: component_updates.validate_component_args REJECTS an
explicit --service-profile on `services updates/update`; product_upgrade argument
validation also rejects it. Therefore put the public preset flag ONLY on baseline
setup/preview. All update/discovery/recovery/product invocations OMIT that flag
and inherit the exact persisted preset; revalidate manifest/plan/case identity
before each child. No parser or public-CLI production change is needed. A missing
or conflicting persisted preset is refusal, never an inferred default.

Public fixed command sequence for component cases:
`services updates --services <literal>`;
`services update --services <literal> [--to <fixed-single-ID>] --preview --json`;
same with `--live --approve-live --json`; repeat; then existing setup/deployment
verification where required. Recovery uses original literal selection with
`--recover`, no `--to`, preview then live; partial batches must stop later writes.
Portainer uses selection `portainer`, target `portainer-ce-2.45.1`, alone.

Fault exercise uses one fixed checkpoint predicate and the actual durable journal,
not patched lifecycle methods, journal contents or injected observations. Observe
the actual stage while the owned gated child is running, signal only that known
Popen group, settle the entire group, then independently inspect real runtime and
journal. If the intended interruption window was missed, report NOT_EXERCISED;
never label successful completion a failure test or downgrade a settled upgrade.
No automatic retries. Additional attempt needs a fresh case intent/GO and baseline.
For Portainer require the actual committed backup checksum before fault arming;
for product distinguish interrupted pre-switch from post-activation observation.

## Honest official-v1 baseline and cleanup

Separate root-owned0700 Linux-native case directory; independent clean official
0.4.0 checkout, real official origin, separate hash-locked Python3.12 environment;
management candidate has a separate prepared Python3.12 environment. Pre-stage
official target/ref and dependencies without altering release refs or the old
checkout. Existing image cache/aliases and full profiles remain baseline-bound.
Precreate ONLY this fresh fixture's managed state root0700 before released logger
startup; never chmod an existing unsafe state root. Bind the released resolver's
actual `TSW_LOCAL_TLS_STATE_ROOT` to this case's own private TLS directory and
apply its supported `TSW_INFRA_ROOT` to the reviewed external tree. Both keys
exist in the immutable0.4.0 source; no globally shared TLS default is permitted.

Use actual released `setup run --live --approve-live --json --node-provider
lxc_native --lxc-backend incus` full preset; verify its actual argv/parser before
authoring. No selective flags exist there. Effective external infra must be the
exact official source tree with ONLY accepted typed provider-memory changes;
current product migration policy rejects image/CPU/disk/topology edits. Supply
credential sources through reviewed resolver boundaries; keep source clean.

Require zero existing default-name instances, root volumes and operations, plus
the full immutable campaign baseline before starting. A legacy creation intent
records exact source/infra/config, names, image fingerprint, allowed profile
changes and an empty graph BEFORE released setup. Monitor creation via actual
Incus observations under the exclusive case window; save each real new UUID,
full specification, root-volume association and source command outcome durably.
Do not retrofit scoped markers or manufacture S04 creation checkpoints.

Released setup may create/update shared named `docker-swarm*` profiles. The helper
must admit an exact finite before/expected-after delta from the pinned release's
profile policy, recheck full foreign-consumer graph, and record each change.
Before launching the released CLI, derive its exact possible profile creation
and individual config-set delta from the pinned provider/profile code. Reobserve
EVERY canonical/inherited foreign consumer and its complete effective instance
specification. Existing foreign-consumed profiles are usable ONLY when ALL
potential released writes are exact no-ops and cannot change any foreign
consumer's effective config/devices/routes; otherwise block BEFORE launching the
released writer. This is a pre-launch predicate, not post-hoc detection. No
foreign/shared profile mutation is authorized by the fixture window.

Admit creation only when its name was absent and expected full state was closed
before launch. For own-only admitted changes retain exact original and expected
current values; cleanup restores only under full current-value CAS and fresh
consumer proof. Unknown partial creation, foreign reference introduced during
the case, unexpected profile/instance, lost creation proof or concurrent actor
blocks both use and disposal. No adoption
of a name-only resource. The fixture window's ownership limitation is explicit;
there is no atomic exclusion against unrelated external Incus clients.

Inventory actual complete source components, desired/task images, Swarm/service
IDs, host and logical selection; create a genuine schema1 inventory with real
installation UUID and exact source lock/revision. Independently validate against
official native assets and real source runtime. Inventory file is NOT runtime
proof. Do not call migration-to-v2 helpers or current selective setup on it.

Set `TSW_REPOSITORY_ROOT` to the actual official0.4.0 anchor; use separate
management executable for `product upgrade --to 0.5.0 --adoption-manifest
<own-inventory> --preview --json`, then live/approve. Recovery omits adoption and
uses original checkpoint. Target launcher is only used for target verification;
it does not contain the newer upgrade controller. Product0.5.0 keeps schema1 and
all original installed component image identities.

Legacy disposal is separate and UUID-bound: settle every public child; acquire
actual installation lease; reobserve complete graph/spec/volumes/foreign refs;
stop/delete ONLY proven case-created three nodes and their own root volumes.
Restore only admitted legacy profile deltas via exact current-value CAS, or
delete a proven newly created profile only after no consumers remain. Preserve
networks, pools, caches, original installations and unknown resources. Require
final full campaign baseline equality plus explicit allowed image-cache receipts.
No whole default-project deletion, reset, network flush or original-node action.

## Receipt ABI and truthful results

Retain the existing eight-case ledger schema1 semantics. New campaigns use ledger
schema2 with the SAME four fields and fixed ordered union of TWENTY-FOUR case names (eight original + sixteen above).
Retain seven-field `new-case-stop.json`/OWNED_CASES_DISPOSED; its digest binds the
actual ledger bytes. Producer and GuestSwitch validate the new version together.
Do not append upgrade outcomes under old fresh-case names or silently skip them.
Finish checks all declared journals, outcomes and child groups, zero instances/
root volumes/generated profiles, no operations and complete preservation proof.
ReturnOriginal is safety proof, never evidence that every case passed.

Outcome binds run, source, host, recipe, selection, owner/exposure, actual baseline
and target, public invocations, exit/time, lifecycle journal stages, private proof
digests, all child settlement and final disposal result. Private raw backups,
configs, tokens and credential-bearing archives never enter public records.
Record actual fault stage, before/after auth/data probes, full retained Swagger
bundle, Portainer saved definition/Env/ResourceControl and fresh replicated/global
tasks. No-op requires fresh proof plus unchanged actual mutation/backup/stack-write
counters; discovery's recorded no_op alone is insufficient. Separate PASS from
FAILED_DISPOSED, RECOVERED_DISPOSAL, NOT_EXERCISED and recovery-required.

## Draft preflight GO request (Root/reviewers, not the user)

Authorize SOURCE S-U1 then S-U2 with the exact locks above and independent
requirements/architecture/security/devops/test-evidence review. Before live GO:

- PC nearest tests, real fixture-core delivery tests and all seven QUALITY gates
  on exact frozen bytes; no locally executed project tests by the author.
- Actual two-host S02 artifacts/source applicability and genuine capability
  promotion; matrix stays EMPTY until these exist.
- Immutable candidate/full source tree pins, recipe/input/config/proposal hashes,
  exact actual host/GUID/VHD/machine/boot identity, original-preservation proofs,
  one fixed closed case, operator consent and independent approved GO expiry.
- Pre-stage image source/target complete bundles on intended nodes, real Python
  3.12 management/source/target prerequisites and dependencies, official refs;
  no downloads/package installation hidden inside a maintenance retry.
- Actual resource inspector passes typed10/6/1GiB memory override where allowed;
  no memory reservation success inferred from configuration. Provider disk
  declarations total80GiB (20/50/10); inspect actual free pool/staging/backups
  capacity and current engine guards. Product requires additional2GiB staging
  plus128MiB for bound infrastructure. Portainer requires actual cold-/data backup
  capacity. Original workload headroom must remain sufficient for restoration.
- Adopt these explicit containing phase budgets, rather than silently extending
  the existing child. Actual native base is case5400/START8880; the old6900s figure
  does NOT describe that native supervisor. Existing native phases outside case
  remain prepare1200 + pause600 + approval180 + teardown900 + restore600.

  | Closed forward purpose | Engine case split | WSL total | Native total |
  | --- | --- | --- | --- |
  | component/Portainer qualification | baseline5400 + exercise3600 = case9000 | admission300 + case9000 + disposal900 + final300 =10500 |1200+600+180+9000+900+600 =12480 |
  | official-v1 product qualification | baseline7200 + exercise10800 = case18000 | admission300 + case18000 + disposal900 + final300 =19500 |1200+600+180+18000+900+600 =21480 |

  The closed recipe selects purpose and BOTH containing/phase monotonic deadlines
  BEFORE any child/effect. GO binds the complete exact budget table, source,
  host/case/intent and expiry through required teardown/original restoration.
  Existing eight-case supervisor allowances remain unchanged. No phase borrows,
  per-stage counter reset, expired-child continuation or source-derived arbitrary
  timeout is permitted. Inadequate containing expiry refuses before any effect.

- Engine recovery is a NEW separate fixed invocation mode and phase-specific GO,
  selected BEFORE child start; NEVER extend the old disposal-only recovery.
  Settle any forward child first and reprove the same original case intent,
  installation UUID/profile, exact pending engine journal/backup, source/host and
  complete graph. Fresh recovery authorization binds those originals; it does not
  create a replacement fixture or reinterpret a completed success as a fault.

  | Closed recovery purpose | Public recovery bound | WSL total | Native total |
  | --- | --- | --- | --- |
  | component/Portainer engine recovery |3300 |300+3300+900+300 =4800 |1200+600+180+3300+900+600 =6780 |
  | official-v1 product engine recovery |10800 |300+10800+900+300 =12300 |1200+600+180+10800+900+600 =14280 |

  These distinct fixed mode/GO totals require Root normative authorization before
  implementation/live use. One operation has monotonic total+phase deadlines;
  there is no in-place clock reset on failure. Existing900s disposal-only recovery
  stays EXACTLY900, with unchanged owned scoped disposer, and is safety cleanup
  only. It neither runs product engine recovery nor counts as upgrade recovery
  acceptance. Full journals/backup/unknown ownership survive refusal unchanged.
- Existing native source/provenance/LXD-own-transition protections remain exact;
  WSL coordinator/bridge all-stopped reset/return source contracts remain exact.
  New guest stays the sole selected running registration during case execution.
- A failed/interrupted case retains every original checkpoint, backing archive,
  intent and raw private observation; no auto retry or cleanup on unknown
  outcomes. Recovery only from fresh source/identity/UUID/graph proof. If full
  disposal cannot be proven, hold the new guest/window and report recovery
  required; never restore an overlapping original runtime by assumption.

No approval to reduce W09/W10 acceptance criteria, perform host effects, publish
qualification, alter product compatibility schemas or rewrite historical evidence
is requested by this source proposal.


## R2 independent source-design disposition

This R2 preserves the exact15 file locks and ordered S-U1→S-U2 split. It addresses
Root-accepted findings through real public setup preset binding, all normal batch
tuples, explicit24-case producer/consumer schema2 and full containing budget/GO
semantics. Private source containing actual qualified literals remains unpublished
UNQUALIFIED test input until all declared tuple evidence and independent review.
No synthetic catalog, alternate repository, environment qualification switch,
public guard relaxation or runtime/domain escape hatch is introduced.

Independent review verified the actual current parser allowance/refusals and the
official target's InstallationManifest/build_platform_services/deployment APIs;
no fabricated legacy target API is assumed. Legacy full source/profile writer
and cleanup remain a separately admitted S-U2 prerequisite, with mandatory
pre-launch foreign-consumer/no-op predicate and exact current-value CAS.

Source-only design GO for this precise contract: Root must first record normative
budget/ledger/promotion authority and exact source locks, then release S-U1. This
is not qualification/publication, tests or host permission. S-U2 retains its own
later release. Any actual product incompatibility requires a reported finding and
explicit additional lock approval; authors may not widen these15 paths silently.
