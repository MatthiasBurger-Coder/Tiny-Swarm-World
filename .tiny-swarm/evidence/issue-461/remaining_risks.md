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

Current external prerequisites, 2026-10-11: sourceef7 physical native existing-host
read-only checks and own-venv preparation/rerun are recorded; full installation
and destructive reboot/fault recovery are not authorized on a verified clean
recoverable scope. Existing IPv6 bridge and three nodes remain protected.
The additional native26 fixture failed its recovery boot and is now Off with
clean checkpoint retained; it is not substituted for successful Linux results.
Windows32 fixture remains Off pending both physical and commit headroom. Latest
read-only Windows observation:39.041GiB physical available,29.238GiB commit
available; total commit limit72.291GiB, automatically managed pagefile8806MiB.
User capacity question was answered with actual measured values; no physical-host
pagefile policy or application state was changed. Existing VM-only Ubuntu reset
consent remains valid, but execution has not occurred.

The subsequent operator-authorized 26-GiB resize supersedes the current
Windows32/Off prerequisite above: owned Windows VM now runs at fixed 26 GiB.
Standard WSL 21 GiB plus Windows reserve 7 GiB cannot fit this guest; resource
policy is unchanged. Reset consent remains confined to the protected test VM.

## Current operator-requested Windows allocation: 28 GiB

The subsequent explicit operator request supersedes the 26-GiB allocation:
owned Windows VM was gracefully shut down, resized to fixed 28 GiB, and actually
started successfully. Physical headroom was 38.583 GiB and commit headroom
28.848 GiB before successful Hyper-V allocation. An initial conservative
30-GiB start check did not attempt startup; actual allocation was subsequently
attempted with measured headroom exceeding 28 GiB, with Hyper-V enforcing
hypervisor overhead. No host pagefile or product capacity policy was changed.
See windows28_resize_start_result.json. This verifies fixture resize/start,
not successful product preflight or full issue qualification. Earlier 26-GiB
insufficient-capacity and Windows32/Off observations are historical.

Actual sourceef7 at28: Preflight and DryRun exit2 with
insufficient_host_capacity and bootstrap_state_invalid; protected fingerprints
unchanged. Windows deficit1159168bytes against exact21+7GiB requirement.
The subsequent current recovery-point helper was not launched: Windows
elevation was canceled. No current28 checkpoint was created or restored and
no Ubuntu unregister/reset executed by that helper. Last verified VM state
Running28; original verified operator checkpoint remains retained. User
interactive Windows availability is requested before another elevation attempt.
See windows_recovery_elevation_result.json.

Capacity planning from the unchanged reserve formula: at nominal29GiB the
Windows reserve rises to8GiB, requiring29GiB observed; if the same small guest
reservation remains, exact29 also misses the boundary. Nominal30GiB is the
next whole-GiB setting with arithmetic margin (29GiB required). This is a
planning calculation, not an executed30GiB qualification or operator-approved
resize; current explicit28GiB allocation remains unchanged.

## Explicit operator-requested 30-GiB retry

Operator explicitly requested30GiB and retry. Exact owned VM was gracefully
stopped, resized to fixed30GiB and actually started. Observed pre-start physical
headroom41.078GiB and commit headroom35.187GiB exceeded30GiB. No host pagefile
policy or product resource threshold was changed. Source-bound candidate
preflight/dry-run is pending; this resize/start alone is not qualification.
See windows30_resize_start_result.json. Prior28GiB observations are historical.

Sourceef7 actual30GiB retry: resource_state VERIFIED and
effective_verified=true in both Preflight and DryRun. Observed Windows
32211095552bytes; WSL physical22547132416/usable22033051648bytes,8CPU,
swap6442450944bytes, storage known. Overall both exit2 on
bridge_inventory_unavailable and bootstrap_state_invalid. Protected config,
registrations, hosts and prior-source canonical state remain unchanged.
Capacity blocker is resolved for this observed30GiB fixture, not for earlier
28GiB. No full installation qualification is claimed. See
windows_ef7_30gib_preflight_result.json.

Current30 snapshot actual restore PASS before destructive testing. Exact
checkpoint eaff8dec-c016-421c-b235-5952d6c7c0a4 restored and selected Ubuntu
registration, machine-id/release hashes, WSL configuration, canonical state
and owned marker matched. Separately authorized VM-only Ubuntu terminate and
unregister both exit0; actual empty guest registration inventory observed.
Exact checkpoint was then restored again: measured identity/config/state
hashes matched; primary host WSL registrations/config fingerprints unchanged.
Reset/recovery isolation PASS for the recorded scope, not every Ubuntu file
and not product installation qualification. Original recovery points retained.
See windows30_current_recovery_result.json and
windows30_ubuntu_reset_recovery_result.json.

Read-only bridge diagnosis: actual unmodified bridge inventory subprocess
exit124 at45seconds, cause timeout; no bridge installation executed.
Independent read-only service/firewall/listener/portproxy dependency probes
all exit0 (2211/2906/2226/874ms), so individual inventories alone do not
establish bridge readiness. See windows30_bridge_diagnostic_result.json and
windows30_bridge_dependencies_result.json. Default preparation's15s inventory
refusal remains recorded; no timeout default or safety guard was changed.
