# Epic 440: preserving WSL resource maintenance

State: SOURCE_FROZEN_FOR_INDEPENDENT_REVIEW. Base `5084fc93`. Implementation
authored; PC verification NOT_RUN, live execution NOT_RUN. No host effect claimed. Author is the delegated Windows automation implementer; root
provides independent requirement/architecture/test review and owns verification.

## Slice and locks

Preserving S02/W05 prerequisite maintenance under workflow v1.49 and
`adr-preserving-host-maintenance-for-qualification.adoc`. Locks only:

- `tools/windows/qualification/wsl_resource_maintenance.ps1`
- `tests/fixtures/wsl_resource_maintenance.ps1`
- `tests/tools/test_wsl_resource_maintenance.py`
- `tools/linux/qualification/wsl_guest_inventory.py`
- `tests/tools/test_wsl_guest_inventory.py`
- this record

Existing W05 and bridge source remains unchanged. No eligibility exception,
relay exemption, full bridge refresh, feature operation or new route is added.
The controller is dot-source safe; importing it performs no host action.
An explicit invocation requires a source/host-bound scenario and production
adapter construction. Mock ports exist for independent fault injection; they
cannot be selected by the production command-line entrypoint.

## Concrete transaction

The native Windows parent survives WSL shutdown. It validates a bounded exact
scenario containing source revision/assets, registration identity, sole Ubuntu
registration/running set, 21 GiB/8 CPU/6 GiB intended resources, prestate digests,
bridge identity/configuration, existing owned route tuple set and recovery
reference. Reject unknown fields, malformed types, duplicates and stale hashes
before effects. Authoritative raw prestate remains RAM or the existing protected
native product recovery store; public results contain fixed statuses/counts and
digests only. Existing controller/fixture authority remains private ext4.

1. Validate source, host, registration, resource and guest-preservation prestate.
   Reject another running registration, unknown guest state, recovery journal,
   ownership/adoption conflict, foreign mapped-port listener or source drift.
2. Acquire existing ServiceUpdate then Reconcile mutexes, each <=30 seconds;
   stop only the exact owned bridge if originally Running. Capture its complete
   runtime/configuration identity. Keep originally Stopped stopped. Capture
   complete route/firewall/hosts and protected bridge state under those locks.
3. Run the real preparation application AFTER quiescence. Require exactly the
   `adapt_wsl_resources` action, resource blockers empty, and only the expected
   aggregate `prerequisite_missing` blocker; bind its fresh fingerprint.
   Invoke real W05 Apply once with exact qualification/source/host/recovery
   arguments. Accept only confirmed RESTART_REQUIRED/exit3, one completed
   resource action and no uncertain effects. Do not synthesize an application
   result or replace its state/backup/ACL/CAS implementation.
4. Recheck guest/registration/preservation boundary; perform one trusted
   `wsl --shutdown` (<=60s), require no running distro, and start only selected
   Ubuntu via ordinary default account `/usr/bin/true` (<=120s). No arbitrary
   guest command or another registration start is accepted. Verify actual
   effective/configured resources through production preparation inventory.
5. Reobserve the same registration's fresh nonloopback unicast IPv4. If changed,
   compare-before-write each existing owned v4tov4 tuple, use fixed `netsh ...
   set v4tov4` only (<=30s), then verify exactly that single destination delta
   in the complete table. Preserve foreign entries, family/protocol/listen tuple,
   connectport/count, firewall and hosts. No add/delete/reset/global replay.
   Update only protected state.wslIp through existing authority and atomic I/O,
   with original-state digest CAS; preserve all other fields. Do not fabricate
   discovery readiness or rewrite unrelated timestamp/heartbeat state.
6. Verify guest identities/configuration, exact resource assessment, protected
   owner and full preservation boundary before restoring original bridge runtime
   state. Observe bounded service reconciliation and compare again. Full refresh
   is never invoked. Capture a fresh post-maintenance route baseline for fixtures.

Guest preservation is a mandatory admission port, not inferred from the native
Linux host inventory. The production guest adapter invokes the new guarded WSL guest helper,
reusing the complete native collector/reader structurally in RAM, with all fresh
unit/socket/access/provenance guards and no persisted native-host claim. The
Windows parent independently binds actual host/registration. Every initial and
final instance must be Stopped; no automatic instance start is admitted. Stable
raw detail DTO digests retain config/device/UUID identity without raw export. The controller must refuse missing/unknown proof;
its production adapter may not use a canned success, assumed empty inventory or accept
name-only identity. An unsupported guest restart/recovery requirement is an
explicit pre-effect blocker, not permission to skip the proof.

## Recovery and timeouts

Finally always releases mutexes. Recovery reobserves before each effect and
restores only captured owned bridge runtime state when current route/owner/
registration authority remains valid. Failure after W05 Apply, shutdown or any
partial route change is RECOVERY_REQUIRED until exact current-state recovery is
verified; do not replay Apply, restore a whole table, overwrite concurrent
changes or silently restart a stopped guest instance. Retain controller/recovery intent on verified private ext4 BEFORE shutdown.
Only existing W05 product checkpoint/backup uses its native store exception;
no new controller-authority NTFS store is introduced. The Windows parent holds
raw baseline in RAM. Bound selected-Ubuntu reentry solely to access ext4 recovery
intent is permitted after controller loss; no other distro or instance starts.
No PASS if recovery failed or state is uncertain. Outer Windows process-tree
deadline and an external recovery owner remain required in the host scenario;
PowerShell finally alone is not protection against process termination.

## Meaningful verification

Mock the real host adapter dependencies, not the transaction itself. Verify
source/registration/owner/guest/listener drift refuses before first write;
service originally stopped stays stopped; mutex order and both failure releases;
new resource fingerprint after stop; real preparation ports/application path
performs exactly one W05 action; failed/partial/uncertain Apply never shuts down;
shutdown timeout/relaunch failure/effective mismatch never produce PASS;
one-to-one owned tuple changes preserve all foreign/firewall/hosts state;
duplicate/unknown/changed routes and state CAS drift deny next write; second
mapping failure retains partial obligations; no state-ready fabrication; captured
service restoration and recovery failures; refreshed fixture baseline; raw
canary path/address/ACL/SID/config strings never enter returned diagnostics.

Python test invokes the PowerShell fixture only on Windows interop using the
existing repository test convention. Root alone runs exact-source PC-WSL
typecheck, focused tests and all seven quality gates on the combined image-aware
collector and controller candidate. No tests here. Root must
independently review final source/test hashes, then commit; host scenario review
is a separate future phase and this plan grants no effects.


## Final authored implementation and exact handoff

The six-file stream is implemented, with no production effect stub. The Windows
entrypoint defaults to **Prepare** (read-only); **Execute** requires the exact
ext4-intent SHA and a complete scenario. **Recover** is executable forward
recovery, not an assertion that RECOVERY_REQUIRED already restored state.
It can reenter only the same bound selected Ubuntu when no distro is running,
solely to read the existing private ext4 intent and reobserve the guest. It never
replays W05 Apply or shutdown. It refuses missing/changed foreign rules, a third
IP, source/registration/guest/configuration drift, and completes only existing
owned old/fresh-IP targets and protected state, then restores captured bridge
runtime. Current global config is accepted only unchanged from the original
snapshot or exactly reconstructed with the existing W05 merge from its matching
protected original backup and metadata. Recovery does not restore a global table
or modify global configuration. If resources still need a new reviewed stage,
RECOVERY_RESOURCE_STAGE_REQUIRED is distinct from forward completion.

The ext4 intent contains the scenario fields **except intent_sha256**, plus
bridge_running and the exact recovery object from Prepare. The latter contains
separate guest/OS/service/firewall/hosts/registry-structure/state-static/netsh-layout
bindings, old-IP digest, original resource file/metadata digests and numeric
resource observations. No raw address, firewall/PortProxy rows, SID, ACL or
configuration content is exported. Parent loss or uncertain partial effects
requires a new exact source/scenario GO for Recover. Main finally cannot promise
Ubuntu reentry after a failed relaunch, especially when the bridge was originally
Stopped; that obligation is explicitly handled by the separate Recover command.

The main direct-command budget is 1800 seconds, 256 launches and 64 MiB; a single
independent finally reserve is 600 seconds, 128 launches and 64 MiB. It cannot be
reset repeatedly. Delegated preparation inventory/actions retain their own
existing bounds; each guest proof retains native 300-second/2048-command/16-MiB
limits. Command output size checks are post-capture checks, not a claim of a hard
async memory limiter. A source-bound outer native Windows owned-process deadline
covering main plus recovery and cleanup remains part of the later host scenario.
The real production clock regression covers a stopped bridge, exhausted main
budget before Apply, and recovery using the independent reserve; unknown/partial
network state still blocks restoration.

Before effects, resource eligibility is checked with the real preparation
application; after quiescence it is replanned and its fresh fingerprint is used
for exactly one W05 Apply. Only expected prerequisite_missing accompanies the
single resource action. Complete firewall/hosts and existing route readiness are
admission requirements so resuming the original background reconciler cannot
create missing rules/hosts entries under this IP-only exception. Service stop
uses no Force; running dependents refuse, and starting a stopped foreign
dependency refuses. Original/QUIESCED/pre-effect/restored phases check distinct
runtime and exact/stable protected-state predicates. A resumed service's first
completed loop is observed before final preservation verification.

Netsh show all is captured as actual private bytes. All four address families,
headers, columns and data rows are parsed without silently dropping output;
expected known TCP entries are cross-checked one-to-one with the complete typed
registry snapshot. Unknown metadata/empty registry keys remain in the whole-tree
CAS. Duplicate, extra, missing or unclassifiable netsh rows refuse. Unchanged
routes require byte equality; cumulative owned-IP updates preserve the complete
row projection and non-data/encoding layout. Same registry plus manipulated
show-all output is a regression case. No raw bytes are persisted.

Guest preservation is explicit opt-in **schema6**, structurally reusing the
image-aware native collector/reader only in RAM. Native target text never
establishes Windows identity or appears in the WSL proof. Image/cache rows and
both new detail command types are retained. Only image last_used_at is excluded
from its stable detail digest, and only instance status/status_code/last_used_at
are volatile in instance digest comparisons. Unit/executable data is retained
with MainPID alone excluded across restart; every query still uses fresh
existing provenance checks. All listed AND detailed instances must be Stopped,
and expanded autostart must be literal false, or absent/empty with last power
absent/STOPPED. True, unknown/nonstring forms, or running detail status refuse
before effects. No instance/profile/configuration is changed to obtain admission.

Pinned primary restart semantics:
[Incus 6.0.5 instanceShouldAutoStart](https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incusd/instances.go),
[LXD 5.21.9 instanceShouldAutoStart](https://raw.githubusercontent.com/canonical/lxd/lxd-5.21.9/lxd/instances.go).
The optional LXD start-protection behavior is not used to widen this subset.

Dependency: frozen image-aware collector SHA256
1c6e62b8c3553d1d185ff3243770f28d16583cb5ffc01e4662a76c620edbaccf,
provenance SHA256
96213743fdfaa31a9e75690b5e49a975167f9f7025862b71611633ef894da9d9.
That separate stream was authored/AST checked when bound here; its independent
review, PC gates and committed host-readiness proof remain root obligations.
Do not test the image-aware helper against this worktree's historical schema5
collector without integrating the exact dependency into the aggregate candidate.

Author verification: three Python files AST-parsed only; five code/test files
checked for trailing whitespace. No PowerShell runtime is available locally;
PowerShell AST, focused tests and quality gates are NOT_RUN. Test code includes
mocked orchestration failures, real production module route/state/service
boundaries, resource merge/metadata verification, closed guest-proof forgery
cases, complete netsh corruption cases, main-deadline recovery and forward
recovery partial/complete/reentry/original-stopped/refusal cases. These are test
implementations, not passing acceptance evidence. Root owns all tests and host
phases. No worker host calls or commits.

Frozen implementation/test assets:

- `tools/windows/qualification/wsl_resource_maintenance.ps1`: `2406672e6c39f3f73fd3c03473cba47f17b9847f82ae3681986f557415da71ec`
- `tools/linux/qualification/wsl_guest_inventory.py`: `471a7da92820e9e73afa2bb1c61d49b0f3dd1045cfe38c241f46277830872570`
- `tests/fixtures/wsl_resource_maintenance.ps1`: `3763d4d4ca73438c119109fcc88788e4364162fd1216f90b4dec343a39a24da7`
- `tests/tools/test_wsl_resource_maintenance.py`: `3531d73c01f654ccec58f6ce98f8fc89c49613327d451206f4a71042e43217f9`
- `tests/tools/test_wsl_guest_inventory.py`: `44dc192f1e9120512560750e5f378163c009744aac9a8d4d8377277a55f02389`

## Root initial PC/static verification

Exact92-asset PC WSL R1 typecheck912 files found4 invariant dict-key typing errors in two test details literals; focus/full NOT_RUN. Type logf08da713d3682f5acac9bbd6a66411308fe546114bb9562ea8db3057127828e7 retained on PC. Root annotated both unchanged dict literals as dict[tuple[str,...],str], no source/assertion change. Frozen actual Windows PowerShell Parser.ParseFile of controller2406672e… and fixture3763d4d4… returned0 errors each, hashes checked. This standalone AST probe followed the initial nearest typecheck (rather than preceding it); no runtime effects occurred. PC focused/full rerun pending.

## Root PC R2 failure and reviewed fixture correction

Exact92-asset candidate typecheck912 PASS loge152893b52561d95c79b66a3f78847c6597c0689d1d217a25e15e85160ae3b63. Focused22 tests26.644s failed1 SOURCE_OWNER_MISMATCH; log6e14a788b8c92e90dc9c8d042fd5e8f1212ec3bd32ec81e8d6a82b0c65913692. Full NOT_RUN. WSL-created native fixture directories had a different owner than actual Windows actor. Independent architecture reviewed exact test-only correction: WindowsActor creates fixture child/.git and copies canonical bootstrap/ports using fixed encoded PowerShell, path singlequote escaping. Real production ownership guard remains unchanged; no SID mock/ACL change. Imports cleaned. R3 pending.

R3 typecheck912 PASS samee152893b…; focused22 failed1 UnicodeDecodeError while decoding German Windows PowerShell preparer error; full NOT_RUN. Focusedlog09ab88ed1e05f37132bc3410c53645a924cc4bf4f980d528e99f037451be151c. R4 retains actual errors with explicit UTF8 replacement decoding for harness diagnostics, no assertion/production change.

R4 typecheck912 PASS; focused22 failed1 SOURCE_OWNER_MISMATCH, logdf6009ebea418004dc9b17d39b96a542117e02cebfe01981d3c176b43a4f715d; full NOT_RUN. Separate bounded Windows temporary-directory diagnostic confirmed actual WindowsActor creates directories owned by built-in Administrators (actor_owner false/admin_owner true/noReparse), including parent/native/.git; raw ACL/SID not exported. Fixture initialization now explicitly sets owner to current actor ONLY on the newly created native/.git test directories; production guard stays actual/unmodified. No existing host source ACL change.

## Root final PC R5 qualification

Exact92 assets verified before testexecution. Typecheck912 PASS (e152893b52561d95c79b66a3f78847c6597c0689d1d217a25e15e85160ae3b63); focused22 in29.571s PASS (4b4e4eb58677fe5a8a10bcb27253b3e48ae5fb8bc15f9ae292c953f40dd684f1); all7 QUALITY PASS,3392 discovery in196.329s,36skips, quality8121a20276ebdf3515e88e291582c8cc2d42c245992f0b850efa985065aa837d. Logs retained PC private ext4; tests used isolated HOME and actual WindowsPowerShell production adapter with mocked host effects. Root read controller/guest/preservation/netsh/parser/recovery, independently from author; architecture independently reviewed exact testfixture deltas. Final record changed only to report actual results. No live resource maintenance, restart or host runtime/service acceptance yet.
