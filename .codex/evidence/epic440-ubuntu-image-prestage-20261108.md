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
