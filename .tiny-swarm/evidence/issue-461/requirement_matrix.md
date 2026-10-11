# BOOT-W09 requirement matrix

Issue: [#461](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/461).
Baseline: `0528aac913c37ddfd66fc8f326d5f92505bdd7dd`.
Current frozen runtime candidate: `ef7e88350ede68f7d4197265b2a272c4bd404a3c`. Previous corrected candidate: `bce63aafb6990e9157c8ddb3eb12e4aa9fd1f440`. Historical native/feature runtime: `3da77f8908d598688ed46dd6eab74c5f32a7ac50`.
Dependencies #459 and #460 are CLOSED and integrated. Status: BLOCKED pending
native freshness/restoration and complete live scenario evidence.
This matrix precedes implementation; subsequent live findings extend the explicit remediation scope below.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-01 | Define native Ubuntu 24.04/26.04 x86_64 and Windows 11 + Ubuntu WSL2 matrix with exact Windows/WSL versions | Qualification / qualification_matrix.md | Four release rows and required version fields | Read-only N26/W26 version observation; 24.04 targets absent | PARTIAL |
| R461-02 | Run clean-host preparation and install on both families | Live / per-run evidence | S01 in qualification matrix | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-03 | Run repeated preparation and install | Live / per-run evidence | S02 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-04 | Preserve unrelated Incus and WSL resources | Live / per-run evidence | S03 | Native protected scopes/nodes unchanged; ordinary WSL preservation pending | PARTIAL |
| R461-05 | Exercise resource limits with #440/#444 selection semantics | Live / per-run evidence | S04 | Sourceef7 actual30GiB guest resource assessment VERIFIED: selected21GiB/8CPU/6GiB swap and effective physical/usable RAM independently verified; actual28 refusal retained historically | PARTIAL |
| R461-06 | Cover reboot, selected WSL restart and group refresh | Live / per-run evidence | S05/S06 | Owned Windows guest boot transition verified after confirmed features; selected WSL restart/group refresh still unverified | PARTIAL |
| R461-07 | Cover IP drift and port collision | Live / per-run evidence | S07/S08 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-08 | Cover unavailable downloads and interrupted-run recovery | Live / per-run evidence | S09/S10 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-09 | Verify routes and service authentication | Live / per-run evidence | S11 | Not run; credentials/service target unavailable | BLOCKED |
| R461-10 | Record exact committed SHA, host/tool versions, commands, exits and redacted evidence on authorized restorable targets | Evidence / per-run package | Run record contract in qualification matrix | Native preflight/Python preparation records exist; remaining live runs absent | BLOCKED |
| R461-11 | Reuse #363 only with exact scenario/source applicability; reject dirty/mock qualification | Evidence / applicability review | Historical applicability section | #363 source/scenario differ; no live pass inherited | VERIFIED |
| R461-12 | AC1: Both families have fresh/rerun/recovery results with PASS/PARTIAL/BLOCKED | Acceptance / qualification matrix | Explicit BLOCKED rows | Partial native existing-host results; required fresh/rerun/recovery absent | BLOCKED |
| R461-13 | AC2: Ordinary WSL preservation and separately explicit reset isolation have real evidence | Acceptance / per-run evidence | S03/S12 | Ordinary sourceef7 preflight/dry-run preserves registrations/config/state hashes; Current30 checkpoint actual restore and separately authorized Ubuntu terminate/unregister (exit0, empty guest registration inventory) then exact restore PASS; primary WSL registration/config fingerprints unchanged; ordinary full-apply preservation still open | BLOCKED |
| R461-14 | AC3: Each supported release qualified or explicitly unsupported/unqualified | Acceptance / qualification matrix | Four UNQUALIFIED rows; excluded target families | Static release classification | VERIFIED |
| R461-15 | AC4: Targeted regressions and applicable quality/security gates pass on integrated candidate | Local / test_results.md | Existing unchanged regression suites | Focused 35 tests PASS; original audit FAIL, corrected lock strict audit PASS; full Python 3.12 quality PASS; source/lock frozen byte-equivalent | VERIFIED |
| R461-16 | Map acceptance IDs to meaningful tests/redacted evidence and follow repository completion policy | Governance / six-file package | acceptance_checklist.md and this matrix | Completion audit required; issue stays BLOCKED | PARTIAL |
| R461-17 | Thin entrypoints, application/port reuse, Linux execution; Windows preparation explicitly in scope | Architecture / existing entrypoints | Narrow existing Windows persistence fix; Python boundaries unchanged | Static scope check | VERIFIED |
| R461-18 | Cover plan/apply consent, preservation, rerun, bounded failure and write-free preflight/dry-run | Live and local / existing regression tests, per-run evidence | S02/S03/S08/S09/S10/S13 | Local regressions cannot replace live observations | BLOCKED |
| R461-19 | Avoid duplicating #427, DNS, K3s, Podman or multi-host provisioning | Scope / existing evidence | New bootstrap stages and exact release scenarios only | Static scope check | VERIFIED |

Required live acceptance remains unverified. Actual native exit-2 results are
recorded separately from absent executions; no release is qualified.

## Operator steering and qualification blocker remediation

Historical initial steering, superseded by the later scoped reset consent:
on 2026-10-10 the operator identified the native SSH and local WSL targets,
then authorized tests directly on native Linux and creation of a Hyper-V
Windows test environment. No destructive reset authorization or native clean
snapshot was supplied. Live state must now distinguish granted test scope
from missing recovery/cleanliness prerequisites.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-20 | Remediate observed runtime dependency audit blocker for AC4 without weakening audit | Dependency / requirements.lock | Narrow urllib3 update using Python 3.12 lock generation | New strict audit PASS and full Python 3.12 gate PASS | VERIFIED |
| R461-21 | Use the supplied native target for authorized testing and provision isolated Hyper-V Windows target | Operator scope / protected local VM assets and run evidence | Native bounded Python preparation; isolated Windows OS provisioned | Win boot/source-bound dry-run/checkpoint restore verified; disk now GPT; First feature UAC launch canceled; retry confirmed features with partial checkpoint failure; owned guest recovery reboot verified | PARTIAL |

Declared additional write scope: requirements.lock for the AC4 security
remediation; tools/windows/preparation/Adapters.ps1 and tests/windows/prepare-windows.Tests.ps1 for the reproduced atomic checkpoint replacement failure; protected ignored VM preparation assets/evidence and documentation/user_guide/windows-preparation.md. Product
Python, architecture and bootstrap authorization contracts remain unchanged. A runtime lock
change requires a new committed candidate before qualification. No live mutation
may bypass the requirement for a recoverable target.

| R461-22 | Repair the live-observed durable checkpoint replacement failure so reruns/recovery retain confirmed effect evidence | Live blocker remediation / Adapters.ps1 and prepare-windows.Tests.ps1 | Narrow NullString fix; existing atomic replace and ACL guards retained | Windows PowerShell 5.1 isolated actual writer creates pending but effect replacement raises ArgumentException; direct NullString replacement succeeds; canonical pending state unchanged. Real-filesystem regression fails before fix, passes after fix under pwsh7 and WindowsPowerShell5.1; corrected full Python3.12 quality PASS. Corrected frozen source-bound protected disposable actual writer create/replace PASS with real ACL guards. Product full-stage qualification remains separate. | VERIFIED |

| R461-23 | Resolve the observed selected WSL VHD trust compatibility before resource apply; preserve manual Ubuntu and all guards | Live prerequisite / storage permission trust finding | Metadata-only VHD role correction independently accepted and verified; historical pre-correction refusal retained | Revised source-bound preflight exit2; resource inventory cause untrusted_evidence_acl; canonical state/config unchanged | VERIFIED: source806 full quality/resource apply exit3; historical memory mismatch resolved by sourceef7 actual30GiB resource assessment VERIFIED |

2026-10-11 authorized continuation: R461-23 remediation scope includes
ResourceAdapters.ps1, tests/windows/resource-files.Tests.ps1, the existing
wsl-capacity-adaptation ADR amendment and windows-preparation user guide.
Independent System Architect and Completion Auditor accept metadata-only selected
VHD path-role correction: retain trusted owner, regular-file/no-reparse and strict
BasePath/ancestor checks; no VHD content IO, ACL rewrite or SID-family whitelist.
Evidence/config/swap guards stay unchanged. User separately authorizes destructive
Ubuntu reset ONLY inside the owned test VM AFTER a new verified recovery snapshot.
Primary/local WSL remains outside that authorization. New runtime changes require
new passing gates and frozen committed source before live qualification.

R461-23 test reporting scope also includes tests/test_wsl_resource_projection.py: explicit Windows child-output decoding keeps native localized errors visible rather than raising UnicodeDecodeError. Return-code and PASS assertions stay strict.

| R461-24 | Correct observed WSL physical-versus-usable RAM accounting without weakening capacity limits | Actual source806 restart blocker / architecture approved 2026-10-11 | Two independent observations; normal-zone present pages exclude holes, MemTotal/cgroup clamp retained; exact five-key parser | Full gate PASS2555; targeted19 tests PASS; independent concrete reviews approve; sourceef7 live physical/usable inventory observed, actual30GiB sourceef7 Preflight and DryRun resource_state VERIFIED, effective_verified=true; full install remains blocked on bridge/state | VERIFIED (resource case only) |

R461-24 scope: tools/windows/preparation/linux-resources.sh, Resources.ps1,
tests/windows/resources.Tests.ps1, tests/windows/prepare-windows.Tests.ps1,
tests/test_wsl_resource_projection.py, existing capacity ADR and user guide,
issue461 evidence. Branch fix/boot-w09-live-qualification-20261010; completed
workflow355 is not reopened. No active overlapping execution lock observed.
Architecture reviewer approves based on actual page-size4096 and normal RAM
present5504671 pages; physical22547132416 versus configured22548578304 bytes.
No tolerance increase, node-budget reduction, primary-WSL reset or release claim.

| R461-25 | Normalize actual hosts text observation before bridge inventory fingerprint serialization; retain content-sensitive consent and all ownership/read-only guards | Live timeout remediation / tws-wsl-bridge.ps1 and bridge-preparation.Tests.ps1 | Declared before implementation; exactef7 trace stops at digest ConvertTo-Json depth12 on extended Get-Content string | Direct inventory124/45s; bounded real-file red/green regression; full quality2555PASS; independent concrete reviews approve | LOCAL_VERIFIED / LIVE_OPEN |

R461-25 authorized issue remediation scope: tools/windows/tws-wsl-bridge.ps1,
tests/windows/bridge-preparation.Tests.ps1, existing Windows preparation guide
and issue461 evidence. Existing Python test runner suffices. No workflow355
execution/replacement, timeout increase, ACL/ownership guard change or
credential dialog bypass. Independent architecture review accepts observation
normalization with unchanged encoding/failures; no new ADR needed. Meaningful
regression must compare metadata-bearing equivalent file content and plain
content fingerprints, and retain actual content/newline sensitivity. New
quality/source freeze is required before affected live qualification.
