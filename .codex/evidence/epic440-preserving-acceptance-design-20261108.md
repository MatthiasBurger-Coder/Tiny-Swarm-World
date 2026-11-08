# Epic 440 preserving acceptance implementation design

Status: READY_FOR_WORKFLOW for the bounded prerequisite design below; live
execution remains dependent on implementation, independent reviews, exact-source
PC gates and concrete scenario GO. This is one requirements/architecture/
automation/evidence role pass by the author, not independent multi-role approval.
No hosts, tests or effects were run. Root owns integration and execution.

Source inspected: main 5a6e8c32; frozen S04/S05/S06 integration at 08541b3f
plus 82-pin R2 tuple 20e4d6ee246fc14a1e412468aa8ebc5fde2aef79363af200d18d14884f790e8c.
Parent reports PC R2 type-check PASS on 960 files, log
ff9a51d50310e959f0ca6e65552061a93e7400810d754f544add771328f2f70f.
That result is not live qualification or a whole QUALITY result.

## Authority correction and input facts

The existing 10001 restriction is normative for its original scenario, from
ADR classic-selection-exposure-stack-ownership (Context/Exposure/Consequences),
ADR installation-scoped-incus-profile, workflow449 S07/S08 and context-pack
lines120-124. It is not a permanent product restriction. Renewed user authority
covers completing the Epic and necessary bounded preservation. New exact
service-route scenarios may therefore be designed/reviewed under that task;
they do not expand the current Windows dest-IP-only resource transaction or the
native listener-only callback. No repeat generic user permission is required.
The accompanying proposed ADR precisely separates these scopes.

Local native schema6 inventory, source c4ca086a, 2026-11-07T23:41:04Z:
SHA256 ee7135579e9f441f17c4d8f1fe93a0deb67c94199c6207c4bb9e5b7134e13e8e.
Incus default is empty; issue447-20261024 has its Stopped swarm-manager;
LXD default has three Running original nodes. These are historic facts to
refresh, not current ownership or execution admission.

Local wsl-runtime-window-proposal.json, source df30e7d4:
SHA256 1badf40907c0f7f9c7c753800c2211f48a3fe71e848258ebb264ec02b60279e0.
It binds default/swarm-manager Running, default workers1/2 Stopped and
issue447-20261024/swarm-manager Running, each to distinct UUID digests.
This supersedes the older October statement that WSL default was empty. The
proposal alone proves no installation-manifest ownership and cannot authorize
adoption/deletion. Fresh JIT must inspect actual markers and protected manifests.

The selected least-scope WSL path is a fresh owned registration on the same
Windows physical test host, not temporary relocation of original Incus objects.
Same-default rename fails require_fresh's marker check; cross-project moves
would modify ownership, profiles and root-volume paths. Neither workaround is
needed. Original registration GUID/VHD, project resources, data and snapshots
remain unchanged; ordinary maintenance downtime and restored running states
are recorded separately from data preservation. New distro import and real
bridge rebinding are explicit prerequisite implementations, not assumptions.

## Requirement and delivery matrix

| ID | Requirement/source | Production/qualification owner | Actual state and required work | Verification level | Status |
|---|---|---|---|---|---|
| AT01 | R449-20/32-34; preserving ADR | Native host-maintenance supervisor | Existing narrow pause/finally recovery; add closed product-suite transaction rather than arbitrary callback | Exact-source PC faults plus actual pause/suite/restore evidence | OPEN |
| AT02 | R449-02; fresh guard | Registration-preparation adapter | New authenticated Ubuntu registration; no original instance adoption/deletion or default-name bypass | Actual new GUID/VHD/systemd/Incus and case UUID receipts on approved PC | OPEN |
| AT03 | LCM-04 routes; S07/08 | Protected Windows bridge lifecycle | Custom registration supported in preparation; bridge singleton Distro mismatch requires reversible protected install/upgrade+restore, not refresh | Actual route/service/bundle/heartbeat before/after and restored original access | OPEN |
| AT04 | Fresh cases + AC4 cleanup | Qualification-only disposal adapter | Production post-start cleanup intentionally absent; add exact-created UUID/marker/root/consumer authority | Stop/delete uncertainty, foreign consumers, snapshots and crash/resume plus live removal of only case objects | OPEN |
| AT05 | LCM-02 authoritative supported targets | Canonical transition policy + real lower-level writers | Swagger/Traefik remain candidate; closed own-fixture compatibility proof precedes canonical promotion | Real digests/tasks/readiness/recovery on all advertised host/owner/exposure branches | OPEN |
| AT06 | LCM-01 product upgrade | Existing product controller | Only official v1 0.4.0->0.5.0 pair; fresh current v2 is not Source | Separate real legacy own fixture and current public controller, target verification, recovery/no-op | PARTIAL |
| AT07 | AC1-5 + W10 | Evidence supervisor/independent audit | Unique PID/time/exit/source/run identity; per-case preservation and final P01-15/R449 crosswalk | Actual final per-host scenario ledger, independent audit and owner reconciliation | OPEN |

## Ordered implementation slices

1. **AT-A policy/closed plan contract.** Review proposed ADR and update only the
   conflicting workflow/context route/pause/cleanup clauses with exact scoped
   supersession. Define StrictAcceptancePlan/Case/Recovery models: host,
   registration GUID, original-state digests, effect-source pins, enum scenario,
   exact CLI argv, canonical expected routes, intended fault, actual-owned object
   receipts and finite deadlines. Neither arbitrary callbacks nor policy flags.
   Freeze requirement/architecture/test review before writing effect adapters.

2. **AT-B native product window and disposal.** Keep
   tools/linux/qualification/native_lxd_maintenance.py unchanged for the current
   fixture transaction. Extract/reuse its reviewed stop/restore primitives via a
   focused helper where necessary; new preserving_product_acceptance.py selects
   only a closed product scenario table. Implement owned_case_disposal.py with
   durable transaction-local own-object receipts and its own exact invocation.
   Reuse actual runtime inventory, explicit project=default and host lock; each
   spawned public CLI gets the ordinary installation lease. No command-string
   injection and no nested competing journal claims. Do not enable the legacy
   force-delete helper or product reset/destroy.

3. **AT-C fresh WSL registration and reversible bridge.** A focused Windows
   adapter uses authoritative WSL registration inventory and official verified
   Ubuntu artifact import to a new absent private path. No original export or
   unregister, default-registration or global WSL setting change. Preparation
   already supports custom exact names with explicit UbuntuRelease; inspect
   bootstrap/windows/preparation/Policy.ps1 and Application.ps1. Prepare real
   Incus/systemd/images in the new guest, then run fresh capability/JIT checks.
   Serially quiesce original running workloads with preservation and restore;
   do not assume a distro isolates network or capacity. Bind real custom distro
   source/evidence on ext4. New Windows-source code is confined to the explicitly
   requested host acceptance controller, not ordinary Python domain services.

   The existing actual bridge ConfigReady comparison includes selected distro
   and bundle hashes. Get-BridgePreparationInventory chooses install rather than
   refresh on changed config; refresh/reconcile refuses that install requirement.
   Reuse the protected existing install/upgrade staging/backup lifecycle under a
   new explicit preserving binding transaction and add exact old-binding restore
   with CAS. Service definition/start policy and unrelated Windows rules/hosts
   content remain preserved. No raw protected config/ACL/SID output. Record the
   exact additional tuple set and exposure through preexisting wildcard forwards.
   Require the real service to generate new and restored heartbeat evidence;
   no direct ready-state file or same-IP inference. Production custom-distro
   network preparation must reach the same actual binding, not a test-only mock.

   An owner-unknown bridge/rule collision is an observed NO-GO for that target,
   not permission to replace it. The model identifies the affected authority so
   the existing owning lifecycle can resolve it; foreign rules stay untouched.
   Additional product routes require their separate exact GO; no change to the
   currently frozen resource-window controller or its 10001-only rules.

4. **AT-D real candidate compatibility fixture.** Public catalog stays candidate.
   New closed fixture driver creates its own real Source installation using
   admitted S04/S05 and fully pinned images. Bind only constants from canonical
   component_transitions plus the actual lease/profile operation. Call real
   ManagedComponentRuntime.transition(UpdateStage, consent, recovery=...), which
   dispatches to the same ClassicComponentRuntime/ClassicUpdateWorkflow or
   ManagedStackOperation/GuardedPortainerStackApi used by production. No fabricated
   ComponentUpdateTarget qualification or synthetic UpdateBatch/observations.
   The fixture has its own honest prewrite journal and records that lower-level
   image compatibility, not public batch/persistence, was exercised. Recover real
   Source and verify all tasks before disposal; do not leave manifest/runtime
   disagreement as a successful fixture state.

   Qualify Swagger's retained editor/API/NGINX members plus UI Source/Target and
   Traefik Source/Target. Exercise actual saved Env/definition CAS, admin/API,
   UI/OpenAPI, Traefik TLS/auth, data/config markers, reverse transition and repeat.
   Cover all intended native/WSL, Swarm/Portainer, published/internal branches;
   target policy currently has hosts/presets but no owner/exposure qualification
   dimension, so partial branch evidence cannot silently unlock all branches.
   If narrowing is needed, add an explicit canonical restriction rather than
   a runtime escape hatch. Only independent acceptance of these results permits
   the small canonical qualification delta. Preserve evidence-to-effect hashes;
   rerun PC gates before public acceptance on the final source tuple.

5. **AT-E public acceptance execution.** Each host runs fresh Minimal, fresh
   Swagger and fresh Swagger+Traefik in serial free-name cases. Use own-case
   cleanup and complete preservation comparison between cases. On a suitable
   Source case test Minimal->add Swagger (Portainer-owned), exact persisted
   exposure, ordinary repeat, actual platform/deployment verification and
   service/data/auth/identity invariants. A separate source case exercises
   two actual component transitions, rather than counting a single completed
   component plus a new transition as an all-changing batch.

   Capture actual SIGINT after a durable genuine stage and own CLI process
   settlement; resume the same recorded intent. For genuine partial-batch failure,
   the reviewed fault plan may add an exact temporary unsatisfiable placement
   constraint to the newly owned second service, with full pre-spec identity and
   an exact reversible one-field patch. It affects only fixture tasks, never
   global firewall/daemon state or foreign services. Prove actual first-stage
   commit and second-stage failed convergence, then restore only that placement
   field before supported retry/recovery. Do not classify a pre-admission refusal
   or synthetic journal as a partial batch. Validate this specific fault schedule
   through source review before live; no arbitrary hook or unconstrained racing
   writer is introduced. Old/mixed-task detection must observe real task images.

   On a source Portainer2.45.0 server+agent case with verified API-owned Swagger,
   run the dedicated real2.45.1 upgrade, backup, actual deployment proof, repeat,
   and separately interrupted/API-down recovery. Default2.45.1 is not an upgrade
   source. Keep cold credential-bearing backup private. Negative/no-op/discovery
   cases use actual unchanged before/after evidence, not only an exit code.

6. **AT-F separate real release fixture and W10.** Provision an owned legacy v1
   runtime from the official0.4.0 anchor and independently derive actual adoption
   inventory. Use the current controller and pinned0.5.0 target unchanged. Bind
   real private infra source, selected service inventory, credential references,
   locked environments and original runtime identities; never relabel a v2
   current installation as0.4.0. Exercise actual product stage interruption,
   --recover, final target launcher and literal live no_op. If the pinned legacy
   verifier requires its shared exposure profile, admit that precise fixture
   profile/route contract on the new clean guest/default baseline; do not mutate
   original shared profiles or claim it proves S04's new scoped profile. Native
   legacy fixture must preserve existing shared resources, with actual equality
   before/after; a required incompatible existing profile blocks that particular
   fixture until its separately reviewed own-resource preparation is available.
   Do not modify published releases to force compatibility.

   Refresh every public guide/CLI example against final help and actual results.
   Reconcile all R449 and P01-15 rows, retained historical failures/restoration,
   Q12/Q13 attribution and W07/R35 disposition. Neither closed-not_planned449 nor
   completed450 is evidence; acceptance boxes follow real reviewed artifacts.

## Finite scenario plan and recovery content

A plan contains argv arrays for the actual shipped commands (setup run,
services add/update, product upgrade, platform/deployment verify) and fixed
preview/live/recover variants only. Resolve all targets before pause. Resource
prep, image downloads/builds and Python environment preparation occur in their
own reviewed prerequisite phases, not silently inside an expired fixture GO.
Use command-specific measured upper bounds; do not copy the listener fixture's
900-second budget for product setup. Every execution admission reserves its
whole command, observation, settle, case-disposal and original-restore time.
A dedicated recovery invocation accepts only the original transaction ID and
reobserves actual identity, never a new command or output path. The original
preserve set is immutable; actual created-object receipts are appended durably.
A command timeout does not establish that its effects did not occur.

Node cleanup order: workers2/1 then manager, observed graceful Stop, exact
Stopped UUID/markers/root/snapshot/consumer proof, non-force Delete, verified
absence, generated profile removal only with zero consumers. Shared networks,
pools, images/cache and Issue447 objects are never blanket deleted. If a new
cache has to be retained, record its exact bounded allowed addition rather than
claiming byte equality or deleting a foreign/shared object. Final restoration
requires real original service/runtime usability as well as preserved metadata.

## Delivery estimate and decision

Prerequisite engineering estimate: AT-A0.5-1day, AT-B1-2days, AT-C1-3days,
AT-D1-2days, AT-E/F source/evidence harness1-2days, plus actual serialized
live campaigns and recovery time. These are engineering ranges including absent
foundations, not elapsed wall-clock promises. Reuse may reduce them; host/image/
bridge behavior can increase them. Confidence medium on source interfaces,
low-to-medium on unobserved new registration and route restoration.

Decision READY_FOR_WORKFLOW concerns this closed ordered prerequisite scope.
S02 capability, effect implementation and independent exact-source review must
pass before consumers execute. Overall Epic acceptance remains INCOMPLETE.

Primary WSL sources: https://learn.microsoft.com/windows/wsl/basic-commands
(import/terminate/unregister), https://learn.microsoft.com/windows/wsl/wsl-config
(global versus distro configuration), and
https://wsl.dev/technical-documentation/security/ (shared utility VM and lack
of isolation). The design deliberately does not assume independent per-distro
networks or use unregister as a harmless reset.

## Root incorporation of independent architecture findings

Architecture independently read the complete draft and accepted the finite own-case disposal, separate candidate qualification/promotion and preserving new-registration design, conditional on two explicit preconditions. Root added the exact stopped-new/original-quiesce/owned-bridge-stop/only-original-running/terminate-original/no-running/start-new sequence and reverse restoration, and a separate actual shared-kernel interface/listener/netfilter-owner absence proof before new Incus initialization. No-running alone is not network absence; residual original bridges mean NO-GO, no adoption/delete/flush/global-shutdown fallback. This is still source-planning authority only, not a host/effect GO.

Official Ubuntu24.04.5 WSL amd64 image prefetch is complete locally:388975696 bytes, SHA256bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e. Signed official SHA256SUMS authenticated by exact full primary fingerprint843938DF228D22F7B3742BC0D94AA3F0EFE21092, as independently documented by Canonical. Private metadata/signature logs and image are outside Git. No Windows staging/import/registration/service/network action is attributed to this download.
