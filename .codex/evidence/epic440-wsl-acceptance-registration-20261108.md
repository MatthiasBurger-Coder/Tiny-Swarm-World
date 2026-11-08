# WSL acceptance registration prerequisite — source candidate

Root authorized source-only implementation on base
1e9a65a9 (actual complete base hash is in the candidate manifest). User renewed all-Epic authorization; this is its separately
bounded new-registration prerequisite, not an expansion of the current resource
maintenance transaction. Independent architecture plan review remains pending;
there is no host GO. Root alone runs PC verification and any later live phase.

Four owned paths: tools/windows/qualification/wsl_acceptance_registration.ps1,
tests/fixtures/wsl_acceptance_registration.ps1,
tests/tools/test_wsl_acceptance_registration.py and this record. Other worktrees
and frozen integration assets are not changed by this slice.

## Actual narrow behavior

Modes are Plan, Import and Verify. Production entry accepts only an expected
scenario SHA and a closed base64 scenario. It always constructs real ports;
injected ports are solely the dot-sourced fixture seam. There is no arbitrary
URL, path, executable, argument array, callback or user-facing workflow.

The scenario binds exact operation, explicit decision GO for Import, run UUID,
host, clean committed Git revision, source-pins digest, full original preserve
digest, fixed image SHA/signer identity and finite UTC expiry. Extra/malformed
fields refuse. The caller's expected SHA binds exact input bytes before parsing;
duplicate top-level names refuse. Source is inferred from the script, not CLI.
Existing Preparation source/NTFS/path/ACL/executable/process helpers are reused.
The complete Preparation asset proof plus four fixed helper/test/controller
SHA pins is checked initially, under the import mutex and after real readback.
Preparation source proof executes in a bounded180-second native child, retaining
clean revision/tree/asset checks without an unbounded chain in the parent.

Registration is exactly TSW-Q440-<32-lowerhex-run-id>. Required preexisting private
NTFS parent is ProgramData/TinySwarmWorld/Qualification/AcceptanceRegistrations;
new <run-id> task directory and guest subpath must be absent. Only Import creates
the task directory, gives that new directory a protected inheritable owner/
SYSTEM/Administrators ACL and writes minimal recovery state. It never repairs
ACLs on an existing/foreign path. Plan and Verify create no product state.
Audit/approval/source evidence stays in the original protected WSL ext4 store;
Windows holds only necessary minimal original/receipt identity projections and
digests. No raw firewall, ACL, SID, process environment or secret is exported.

Fixed prepared image path is ProgramData/TinySwarmWorld/Qualification/Images/
ubuntu-26.04.1-wsl-amd64.wsl. Root actually completed the418495746-byte download and verified SHA256
48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104 and signed
official SUMS signer843938DF228D22F7B3742BC0D94AA3F0EFE21092. Runtime rechecks
actual418495746 bytes and digest; it does not claim a new runtime signature or
network download. Signature evidence is Root's private ext4 prerequisite. At
import, the image is held open with Read-only sharing throughout its digest
check and native invocation, excluding simultaneous writes/deletion.

The sole external write is trusted native System32/wsl.exe, valid Microsoft
Authenticode and protected path, exact argv:
--import <derived-name> <fixed-new-guest-path> <fixed-image-path> --version 2.
Import is bounded600 seconds, stdout1MiB, no stderr, with no retry. No start,
terminate, shutdown, unregister, default selection, bridge action, Windows
feature, Incus command, .wslconfig or service/route modification exists here.
Total2400-second/128-child/64MiB budget refuses before a child unless its whole
bound fits; no silent timeout clamp. GO has2400..3600 seconds at initial admission
and at least1200 before import. The sole import receives its full600 seconds.
Private recovery descriptors survive timeout/controller loss.

## Preservation and durable identity

Read actual current-user registration keys/values and their types, authoritative
default GUID, original running-name set and native NTFS VHD identities. Reject
missing, duplicate, unsupported or ambiguous identities. Every original registry
projection, basepath digest, VHD FileID/volume identity and running state must
remain equal. Original running VHD contents are not hashed or represented as
bitwise equal; no original VHD/instance/data write is performed by this helper.

Read-only global preservation includes the complete reviewed ActiveStore firewall
snapshot, netsh show-all output, bridge service definition/start/account/state,
protected bridge bundle file hashes, hosts and .wslconfig. The bridge's ordinary
heartbeat file is excluded as operational state; its protected bundle and actual
service state remain bound. All output is hashed in memory. File traversal is
bounded and checks each child for unsafe ACL/reparse state before descent.

Source dependency is explicit: the corrected complete bulk firewall getter
Get-WslMaintenanceFirewallCommand must be present in the source-bound existing
wsl_resource_maintenance.ps1. Base1e9 alone predates it. Missing dependency refuses
before host effects; there is no old per-rule, partial-store or WQL fallback.
Root must merge the independently reviewed firewall-bulk candidate before this
slice is runnable in production. This worker did not copy/edit that worktree.

Under a dedicated nonblocking mutex re-observe original preservation and check
absence immediately before creating the own intent. Durable private JSON intent
is atomically saved and then changed to import_pending BEFORE native import.
Writes use fresh temporary files, flush, owner-only ACL and expected-state CAS.
A pending or existing record never triggers another import. No auto-unregister
or delete-by-prefix is available.

After native return require all original projections unchanged and exactly one
new actual registration GUID, matching the derived name, fixed new path and
version2, initially Stopped. Record actual NTFS VHD identity plus bounded actual
new stopped VHD/rootfs SHA256. This digest binds that resulting imported disk;
it is not an invented deterministic digest of a freshly generated filesystem.
Only an atomically saved real receipt yields IMPORTED_STOPPED. Verify rechecks
that exact receipt and baseline with source checks, without starting the guest
or updating the receipt. It is not OS/Incus/application readiness.

Lost response, changed state, partial import or receipt uncertainty leaves
RECOVERY_REQUIRED and original private intent/pending state; import is never
replayed. Verify requires a durable verified receipt, so an unknown-outcome
import cannot be promoted through a fabricated same-name read. A separately
reviewed recovery decision is required for such a retained target. All later
use remains gated on the durable actual receipt and its own subsequent scenario.

## Authored verification and limits

Fixture exercises the real orchestration/validation functions with fake source,
registry/filesystem/process boundaries only: Plan/Verify zero writes, exact
write-ahead ordering, receipt-before-verified, import/replay refusal, source/host/
pins/image/executable/ACL/path/storage failures, stale GO, race, failed pending
write, timeout, lost receipt, original registry/VHD/default/running/global drift,
extra/duplicate/new-running/wrong-version/wrong-path/unknown identity and private
error redaction. Actual production ImportGuest AST asserts its fixed argv and
absence of extra effect verbs plus read-locked digest verification. Fixture
output explicitly reports actual_import=false and services_verified=false.
This is authored coverage, not exercised production Windows adapters or live
registration qualification. Native source/ACL/provider/format/performance still
need independent source review, exact-source PC tests/gates and separate host GO.

Author only parsed the Python executor AST and inspected diff whitespace. No
PowerShell/parser/unit/quality tests, runtime imports, Windows staging, host
access, image import, commit or publication by this author. No existing resource
preservation, new registration or Epic completion PASS is claimed.

## PC fixture R1 correction

Root's actual PC WSL nearest test stopped `plan_effect`; retained log SHA256
29b6e2e82d4a3fbec4ccb8ca5956f9cc003b9272616691b3be35c2f9020e47f9.
A separate pure Windows command-resolution observation confirmed `Copy` resolves
to the standard Copy-Item alias even after the fixture declares function Copy.
Rename only the fixture's pure copy helper and calls to the unambiguous
Copy-RegistrationFixtureValue. Production source and assertions remain unchanged.
This is a source correction; R2 checks remain pending.

## Shared certificate consumer amendment (Root source-design470c141f)

Only certificate consumer/contract changes: parameterless shared certificate loader
replaces raw firewall transport; exact8key reader validates complete source-bound
certificate, then GlobalProof hashes it with all unchanged routes/service/files.
Fake actual production transport tests prove8 fresh calls, small bounded output,
changed same-count fullhash detection, malformed and oversized refusal. No image
input/registration authority/effects/recovery policy changed. Root will separately
repin the signed image after this freeze. These new tests are authored NOT_RUN;
no host effects/queries or live registration by this author.

Root serial host-image repin: signed official Ubuntu 26.04.1 WSL image,
418495746 bytes, SHA256
`48d56724b5c8e60f24893e83e73bbb58c60b3ca22fba3da977075420acd54104`,
verified Ubuntu CD image signer `843938DF228D22F7B3742BC0D94AA3F0EFE21092`.
The signed Resolute package index supplies Incus 6.0.5-8, matching the required
provider. This changes only the separately imported WSL host; the fixed Ubuntu
24.04 container image remains unchanged. No import or guest start executed.
