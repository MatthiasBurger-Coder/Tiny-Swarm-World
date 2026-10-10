# Implementation summary

Issue status: IN_PROGRESS, not complete. Current frozen runtime candidate:
`806a58c36aabf8a95601f2bbfb2978e2d6ee2995`; RAM-accounting amendment under verification.
Historical corrected checkpoint candidate: `bce63aafb6990e9157c8ddb3eb12e4aa9fd1f440`. Historical native/feature candidate:
`3da77f8908d598688ed46dd6eab74c5f32a7ac50`, based on integrated #459/#460.
The narrow urllib3 lock correction passes strict audit and full Python 3.12
quality. A live checkpoint persistence defect is implemented, verified and frozen in the existing Windows adapter; product Python is unchanged. The existing completed #355
workflow was not executed or replaced. Branch:
fix/boot-w09-live-qualification-20261010.

Authorized native existing-host tests prepared an owned Python venv and isolated
checkpoint state, preserving eight/nine measured existing file scopes and three
running nodes. Network preparation blocked on existing IPv6-enabled bridges.
Native fresh-host and recoverable fault-test prerequisites remain missing.

The authorized isolated Hyper-V Windows environment now boots Windows 11
Enterprise Evaluation 26H2 build 26300.9457. Windows OS-only provisioning used
24 GiB; answer credentials were removed and verified absent. A scoped owned-VM
storage ACL repair preserved the private parent ACL. Its clean pre-WSL checkpoint
was subsequently restored and booted with matching version, absent candidate
marker, no WSL and VirtualMachinePlatform Disabled. This verifies environment
recovery only. The guest stopped normally and 32-GiB RAM was set and observed.

Source-bound guest dry-run verified the frozen SHA and exited 2 with only
Windows feature prerequisites pending; measured configuration/registration
invariants were unchanged (partial S13). The prepared full 32-GiB feature-only
phase retains the 34-GiB free-host guard. The first UAC launch was canceled
(host exit 1). The authorized retry passed that guard at 34.676 GiB, booted
the full guest, and confirmed enable_features. Apply returned exit 4 PARTIAL
because effect checkpoint persistence failed. Independent inventory and saved
effect evidence confirmed both features Enabled and a pending Windows reboot.
A separate owned-guest recovery restart verified the boot transition and exact
source; post-restart dry-run exits 2 with only install_wsl pending.

A protected disposable-directory reproduction preserves the canonical pending
checkpoint and identifies PowerShell null argument conversion at File.Replace.
The narrow NullString correction preserves atomic replacement and all ACL/state
guards. A new real-filesystem regression passes under Windows PowerShell 5.1.
The revised candidate passes the full Python 3.12 quality retry and the Windows
PowerShell 5.1 filesystem regression. Corrected source is now locally frozen at bce63aaf; source-bound read-only
plan and actual protected disposable checkpoint writer verification pass.
Corrected product apply remains unexecuted. The original failed gate remains recorded.

The operator then manually installed WSL/Ubuntu in the owned VM. Read-only
inspection confirms WSL 3.0.1.0 and running Ubuntu 26.04.1 LTS/x86_64/systemd.
Its approximately 16-GiB WSL memory and 12 processors still need the selected
21-GiB/8-processor allocation. Preserve this operator-created registration;
manual prerequisites do not count as candidate-executed install qualification.

All releases remain UNQUALIFIED. AC1/AC2 and the required product install,
rerun, recovery, preservation/reset and authentication scenarios remain open.
Separate destructive WSL reset authorization was absent at this historical stage;
the later explicit scoped authorization and verified recovery point are recorded below. No issue close,
push, PR or merge is implied by the local verification/environment progress.

Current revised plan exits 2 with resource_inventory_unknown and
bootstrap_state_invalid, no actions. The old identity-bound pending checkpoint
is retained. Resource diagnosis identifies untrusted_evidence_acl on the selected
WSL VHD: observed extra FullControl grants are categorized from SID families as
VirtualMachineInstance and AppCapability. The selected registration directory
has only current-user/SYSTEM/Administrators grants. Resource trust compatibility
needs a reviewed security/architecture decision; no permission rule, ACL, WSL
configuration, distribution or old state identity was changed to bypass it.

## Authorized VHD metadata correction continuation

Actual WSL-managed VHD access grants triggered the evidence-file ACL guard despite
resource inventory only observing presence/type and capacity on BasePath. Independent
System Architect and Completion Auditor accepted a VHD-specific metadata helper:
local NTFS, strict BasePath/ancestor permissions, regular non-reparse file and trusted
owner remain required. No VHD content IO, permission mutation or SID whitelist.
Evidence/configuration/swap ACL guards remain strict. Existing capacity ADR gains a
dated amendment and operator guide clarifies this role. Actual Windows PowerShell5.1
fixture PASS30; modern portable7.6.6 metadata-only fixture PASS10. The full gate is
pending at this writing; no corrected live source qualification is yet claimed.

New checkpoint preserves operator-created Ubuntu; actual restore verification is
pending. User separately authorizes reset exclusively inside this recovered test VM.

R461-23 final local gate PASS; independently reviewed correction is ready for
new committed source freeze. Actual live resource verification remains pending.

## Current resource and secured recovery evidence

Source806 passes full quality and actual source-bound resource apply: exit3
RESTART_REQUIRED, confirmed durable checkpoint, no uncertain actions, selected
21GiB/8CPU/6GiB swap config. New operator-created Ubuntu checkpoint419a8422
was actually restored and verified before the separately authorized VM-only reset.
The original old-source checkpoint was archived under the canonical lock with
bytes/hash/ACL preserved, not edited or implicitly reused. One private operator
helper supplied an unsupported -Apply switch and failed before configuration
mutation; the corrected default-apply helper recorded the actual result.

An actual owned WSL shutdown/start confirms8CPU and6GiB swap, but the old RAM
comparison refuses kernel reservations. Read-only present-page observation
separates22547132416 physical bytes from22033063936 usable bytes. Independent
architecture/security review approves R461-24 measurement correction with
unchanged tolerance and independent MemTotal/cgroup floor. New exact source/live
verification remains required. No release is qualified.

Fresh isolated Ubuntu24/26 native-kernel Hyper-V test guests were provisioned
from Canonical SHA/signature-verified cloud images, fixed32GiB/12CPU/256GiB.
This is a virtualized native Linux test environment; product provider remains
Incus. Guest boot, fresh preparation/install and recovery evidence remain pending.
