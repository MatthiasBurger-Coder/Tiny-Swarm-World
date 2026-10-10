# Remaining risks and blockers

- Native tests and the isolated Windows VM are authorized. The native supplied
  host is an existing installation without a clean OS snapshot/restore proof;
  it cannot establish fresh-host or safe injected-failure recovery results.
- Native Python preparation succeeded in the owned source, preserving existing
  protected scopes and three nodes. Network preparation refused the existing
  IPv6-enabled bridge policy. Preserve that policy; installation needs a
  compatible separately recoverable target.
- No native Ubuntu 24.04 target is supplied. The isolated Windows guest now has
  observed Windows 11 Enterprise Evaluation 26H2 build 26300.9457 and a verified
  clean pre-WSL checkpoint restore. Manual WSL/Ubuntu prerequisites are observed. Candidate-executed WSL/distro/tool installation and full selected
  service capacity remain unverified.
- The 24-GiB Windows OS-only phase is distinct from the full 32-GiB guest. RAM
  was set/observed 32 GiB while off; a 34-GiB free-host guard precedes its boot.
  Do not infer effective WSL limits or service capacity from VM settings.
- User separately authorized destructive Ubuntu reset only inside the owned VM after a new verified recovery snapshot; execution remains pending. Existing local WSL
  distributions and native resources are preserved. Host-wide shutdown/reset
  or native fault/reboot injection must not be inferred from access details.
- All required AC1/AC2 product fresh/rerun/recovery, ordinary WSL preservation,
  reset isolation, routes and authentication results remain open. No release
  support guard or qualified list is changed; #461 remains BLOCKED.
- AC4 is verified locally: urllib3 2.8.0 strict audit and complete Python 3.12
  quality passed at the frozen runtime candidate. Historical failed audit and
  mounted-checkout timeout remain in test_results.md.
- Historical #363 source/scenario results do not qualify this new candidate.
- Authentication requires protected credentials and redacted evidence. Raw
  VM files, credentials, paths and logs remain private ignored artifacts.
- The source-bound Windows dry-run measured only file hashes and selected
  registry fields; it is partial S13 evidence, not comprehensive no-write proof.

No product quality rule, source guard or selected-service capacity requirement
was weakened. Windows OS provisioning at 24 GiB does not qualify WSL capacity.

The first feature-only UAC launch was canceled; the authorized retry confirmed
features but returned exit 4 PARTIAL when the effect checkpoint replacement
failed. The pending checkpoint and effect records are preserved. A separate
owned-guest reboot was verified and fresh source-bound inventory requests
install_wsl. The revised NullString fix has a passing Windows PowerShell 5.1
filesystem regression, and the full Python 3.12 quality retry passes. Corrected source is frozen at bce63aaf and verified in the owned guest.
Protected disposable actual writer create/replace passes; revised product apply
is blocked by storage ACL trust and the retained old-source checkpoint. The operator-installed
Ubuntu registration must be preserved; its observed WSL allocation needs
21-GiB/8-processor reconciliation. Do not upgrade the original partial result.

Current concrete blocker: the selected WSL VHD carries additional explicit
FullControl grants categorized from SIDs as a VM instance and an app capability.
The existing resource path ACL guard refuses them (untrusted_evidence_acl),
leaving storage/effective resource inventory unverified. Independent architecture/security review accepts a narrowly scoped metadata-only VHD role correction with trusted owner/type/path checks; implementation is under verification. Do not remove
WSL-managed grants or permit arbitrary SID families to make the plan pass.
The exact known old-source checkpoint could be deliberately archived with
verified bytes/ACLs and the canonical lock, as independently reviewed; it was
not archived because the independent storage blocker remains. Operator manual
Ubuntu installation, current .wslconfig and canonical pending state are preserved.
