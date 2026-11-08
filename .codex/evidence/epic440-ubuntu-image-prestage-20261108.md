# Ubuntu24.04 exact image prestager — source-only

Base a75160bc; isolated fix/epic440-ubuntu-prestage-20261108. Root owns tests,
hosts, integration and any later live authorization. No host effects or tests here.
Locks: tools/linux/qualification/ubuntu_image_prestage.py,
tests/tools/test_ubuntu_image_prestage.py, this record.

| Requirement | Implementation/test boundary |
|---|---|
| Exact public image, HTTPS+SHA only | Fixed metadata680B/rootfs141541376B SHA256 and combined Incus fingerprint; no GPG authenticity claim. Streaming64KiB fd reads, size/hash/identity stability, no32MiB whole-file read. |
| Root/local/source authority | Existing native inventory unit/executable/socket/root-peer/full-access/server proof, exact6.0.5; fixed run/varlib endpoint with no fallback. Root-owned clean pinned checkout and private ext4 state/input paths, source/hash recheck before effects. |
| Full preservation | Before/after all projects' complete image and alias DTOs, exact unknown-field/type guards, existing rows unchanged; only the pinned image and exact default alias may be added. No nodes/profiles/services/other aliases touched. |
| Alias collision/refuse | ubuntu-24.04 must be absent or point to exact fingerprint; same already present image reused after exact Ubuntu image metadata proof. No same-name adoption, overwrite, deletes or implicit foreign image ownership. |
| Durable uncertain effects | Exclusive private proposal+intent, CAS/atomic durable checkpoints before import and alias writes, full readback after each; explicit read-only reconcile after uncertainty, never blind replay. |
| Pre-baseline only | Separate prerequisite tool; never invoked during a maintenance pause or from product lifecycle. Image-store/cache addition explicitly allowed only for pinned image before any baseline capture; no service/runtime readiness claim. |

Reference: reviewed private Alpine importer /tmp/epic440-fixture-image-import-r2.py.
Its old32MiB whole-file helper cannot accept this rootfs; the new helper streams the
exact141541376-byte input instead. Existing Incus inventory parsers/guard functions
are reused, not replaced by a new runtime discovery engine. Native command/output/
wall bounds remain explicit; failed/timed-out import is uncertain and needs readback.

Pinned fingerprint21c802d47e64cedcf7153503a1b5dbcc8821919b2af993646756868b775a5383;
metadata58eb156ee168ce406ec7c0ed6501b79c44d9e6962db373e937b71656cbdad687;
rootfs7857e5e4edaa70e0c3f7cb7da51e1984ebca79d6314443eba44c34c38b9983a3.
Public input source https://images.linuxcontainers.org/images/ubuntu/noble/amd64/default/20261107_07:42/.
Local cache /home/micro/tsw440-ubuntu-incus-image-20261108 reports SHA-verified,
signature_verified=false, import NOT_RUN. That cache record is input evidence,
not live host import or service proof.

## Implemented source-only handoff

Explicit Root scope GO received for all three locks. Source includes prepare, execute
and read-only runtime reconcile; pending journal stages refuse execute replay.
The shared native maintenance lock excludes its pause; callers must schedule this
prerequisite before a NEW baseline/window, never reuse an older baseline afterward.
No image start/cache-engine/storage sweep is introduced. Result states the exact
allowed cache fingerprint and baseline_recapture_required=true; it does not claim
that cache contents, product services or guest readiness were verified.

Full image/alias collections include inherited default views and independently
owned projects. Alias/Image reciprocity and canonical inherited-view equality are
checked. Only the desired default alias addition is normalized out of its target
image digest; preexisting aliases and all other image metadata remain compared.
Private durable records retain hashes/closed flags, not raw project/config/certificate
values. Digests compare identity; they are not encryption or authentication.

Source must run from a clean ROOT-OWNED clone under trusted root-owned ancestors;
the developer worktree and original micro-owned download cache are not live inputs.
Stage copied exact files into a root-owned0700 ext4 directory with0600 files.
The runtime uses accepted Incus6.0.5 system-unit/executable/socket proof plus an
actual SO_PEERCRED root UID and exact observed daemon MainPID, no endpoint fallback.
Git filter/process/fsmonitor execution is suppressed per invocation. Both input
file hashes and combined fingerprint are streamed again before each runtime effect.
Existing native Runner bounds30s per command/300s total/2048commands/2MiB streams/
16MiB output remain; a timeout is uncertain, not automatic retry.

Primary alias contract: https://raw.githubusercontent.com/lxc/incus/v6.0.5/cmd/incus/image_alias.go
uses CreateImageAlias, no replace/delete; DTO fields are pinned in
https://raw.githubusercontent.com/lxc/incus/v6.0.5/shared/api/image.go.

Authored tests cover an actual sparse141541376B bounded streaming read, size/hash/
symlink refusal, exact fingerprints, full real DTO parser workflow with foreign/
inherited images and aliases, already-present no-op, collision/prestate drift,
import/alias lost responses and no replay, durable CAS, redaction and root-peer
refusal. Low-level runtime transports are synthetic; no host changes or tests ran.

Static AST parsing and git diff --check PASS. Typecheck/tests/quality/live: NOT_RUN
by worker. No commits. Root independently reviews exact candidate then owns PC
verification and any separately authorized live prestaging.

Source/test SHA256:
- tools/linux/qualification/ubuntu_image_prestage.py: 1db2725fe33cb0b1e97361973cb229f05182c88153629d927e936d18e4adf73d
- tests/tools/test_ubuntu_image_prestage.py: 80e7446923f343ceb73c391a9f21098e97e5dc39cc792e7a0c6486e659201e69

## Root PC R2 fixture type refinement

R1 nearest11 tests PASS1.606s, log6c1fb14b3cb15c01f71675cc8c4c01a0d797bb071e91b59d3dea4a31868d68e5.
Typecheck refused one synthetic server environment dict inferred as str-only;
annotate it dict[str,Any] to match the validated heterogeneous API DTO. No
production or runtime-expression change. Retained type failure522b4ee2ae47bb2808043959ee86b7259c9a14db79308e356e2821ffe1efde4e.
R2 type/full checks remain pending.

R2 nearest11 andtype919 PASS. Full quality stopped at one unused json test
import (log1b24d463ec43a972942ae1955026efaf06e7ef2c1f834a8582a2b63f245fdf15).
Remove only that unused import for R3; no source behavior/guard/test assertion change.

## Socket activation correction — approved source-only plan

New isolated stream base176e38e7; same three file locks. Root actual prepare
refused INCUS_ROOT_PEER_CHANGED before any image/alias effect. Sanitized proof
showed root peer PID1, trusted systemd, unchanged active Incus service and exact
varlib socket. This failure is retained; it is not an import success.

| Requirement | Implementation and regression |
|---|---|
| Preserve direct daemon peer | Root peer equal to unchanged exact int MainPID>1 remains supported for either fixed endpoint. |
| Admit only proven activation peer | Root PID1 additionally needs loaded active listening/running exact bound socket, trusted canonical systemd executable, bounded root-only process status; every other PID/UID refuses. Negatives exercise each condition. |
| Full API identity | Private fixed /1.0 proof uses same Runner/budgets, strict sync envelope + pinned Incus6.0.5 trusted/default/noncluster DTO, exact server_pid==initial.MainPID before projection. No guard/query recursion. Malformed, wrong PID and drift refuse. |
| Fresh pre/post checks | Existing guard calls around every API/effect remain. PID1 full activation and root proof repeat each time; no remembered PID1 exemption. Transport tests assert both boundaries and no effect after failed proof. |
| Preserve all other limits/effects | No shared parser changes, no endpoint fallback, unchanged300s/2048commands/16MiB and existing import/alias-only durable recovery. Root owns tests/hosts/commits. |

Root explicitly released this exact plan including the new API PID crosscheck.
The previous shared validator validated server_pid type but did not compare it to
MainPID; this amendment adds that comparison honestly rather than claiming an
already existing binding. WSL reference is fixed fresh_runtime/validate_peer in
the prior reviewed runtime-window controller; this does not infer host behavior
from a fixture or grant any live authorization.

Implementation handoff: direct-daemon peer retains its previous path. Only PID1
executes the added activation and fixed root proof in every guard. The source
reuses the unchanged strict sync-envelope decoder for both guarded public fixed
queries and the nonrecursive private /1.0 primitive. Root proof fully validates
the family DTO before comparing actual server_pid with the captured service PID;
snapshot performs the same crosscheck before its projection. Both endpoint forms
remain finite and bound, without run/varlib fallback. Additional root reads are
charged to the SAME existing Runner; no budget reset or raise is introduced.

Authored seven new regressions cover direct root daemon on both endpoints, PID1
proof on both endpoints, other/nonroot peers denied before API, bounded/root-only
systemd process/status and listener refusals, malformed/wrong-authority/root-PID
DTO and sync-envelope failures before effects, and actual guard/query/effect
transport order proving two fresh PID1/root checks around each operation. These
are synthetic transport tests; no daemon, import or alias command was executed.

Static AST parse and git diff --check PASS for this correction. Test/type/full
verification, host execution and commits NOT_RUN by worker. Root owns independent
review and PC gates before a separately authorized fresh prestage. The actual
INCUS_ROOT_PEER_CHANGED refusal remains retained and had no effects. No earlier
prepare/proposal is upgraded by this code change; a fresh source-bound proposal
and new baseline after any successful import are still required.

## Socket activation correction: Root integration evidence

Actual native prepare on exact176e38e7 source refused INCUS_ROOT_PEER_CHANGED
before any image/alias effect. Read-only binding diagnosis proved root PID1 peer,
trusted systemd, exact loaded active/running Incus service/socket and fixed
var-lib endpoint. The narrow reviewed activation proof retains all original
source/API/metadata/budget constraints and adds actual root server-PID binding.

PC SSH/WSL `epic440-prestage-activation-20261108-r2`, base7523f85b, three exact
R2 paths:17 nearest tests PASS1.934s,type978 PASS, all7 quality PASS,
3625 tests/36 skipped/283.967s. Full quality log SHA256
`a3a7afefecef48e09c54316d16f8d97ed9a2f8a046c210e5a616bdeee1bea5e1`.
R1 typecheck rejected optional dictionary key; RootR2 adds an explicit string
endpoint guard. Independent source reviewer preflight_review approved original
activation semantics; Root reviewed this strengthening. Actual import/alias
remain NOT_RUN and require a fresh before-baseline plan.
