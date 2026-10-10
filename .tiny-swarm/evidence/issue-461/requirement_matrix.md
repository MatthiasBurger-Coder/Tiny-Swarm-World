# BOOT-W09 requirement matrix

Issue: [#461](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/461).
Baseline: `0528aac913c37ddfd66fc8f326d5f92505bdd7dd`.
Frozen runtime candidate: `3da77f8908d598688ed46dd6eab74c5f32a7ac50`.
Dependencies #459 and #460 are CLOSED and integrated. Status: BLOCKED pending
native freshness/restoration and complete live scenario evidence.
This matrix precedes implementation; subsequent live findings extend the explicit remediation scope below.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-01 | Define native Ubuntu 24.04/26.04 x86_64 and Windows 11 + Ubuntu WSL2 matrix with exact Windows/WSL versions | Qualification / qualification_matrix.md | Four release rows and required version fields | Read-only N26/W26 version observation; 24.04 targets absent | PARTIAL |
| R461-02 | Run clean-host preparation and install on both families | Live / per-run evidence | S01 in qualification matrix | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-03 | Run repeated preparation and install | Live / per-run evidence | S02 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-04 | Preserve unrelated Incus and WSL resources | Live / per-run evidence | S03 | Native protected scopes/nodes unchanged; ordinary WSL preservation pending | PARTIAL |
| R461-05 | Exercise resource limits with #440/#444 selection semantics | Live / per-run evidence | S04 | Not run; target capacity/selection absent | BLOCKED |
| R461-06 | Cover reboot, selected WSL restart and group refresh | Live / per-run evidence | S05/S06 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-07 | Cover IP drift and port collision | Live / per-run evidence | S07/S08 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-08 | Cover unavailable downloads and interrupted-run recovery | Live / per-run evidence | S09/S10 | Not run; recoverability/runtime prerequisites missing | BLOCKED |
| R461-09 | Verify routes and service authentication | Live / per-run evidence | S11 | Not run; credentials/service target unavailable | BLOCKED |
| R461-10 | Record exact committed SHA, host/tool versions, commands, exits and redacted evidence on authorized restorable targets | Evidence / per-run package | Run record contract in qualification matrix | Native preflight/Python preparation records exist; remaining live runs absent | BLOCKED |
| R461-11 | Reuse #363 only with exact scenario/source applicability; reject dirty/mock qualification | Evidence / applicability review | Historical applicability section | #363 source/scenario differ; no live pass inherited | VERIFIED |
| R461-12 | AC1: Both families have fresh/rerun/recovery results with PASS/PARTIAL/BLOCKED | Acceptance / qualification matrix | Explicit BLOCKED rows | Partial native existing-host results; required fresh/rerun/recovery absent | BLOCKED |
| R461-13 | AC2: Ordinary WSL preservation and separately explicit reset isolation have real evidence | Acceptance / per-run evidence | S03/S12 | Ordinary owned-guest testing authorized but pending; explicit reset consent missing | BLOCKED |
| R461-14 | AC3: Each supported release qualified or explicitly unsupported/unqualified | Acceptance / qualification matrix | Four UNQUALIFIED rows; excluded target families | Static release classification | VERIFIED |
| R461-15 | AC4: Targeted regressions and applicable quality/security gates pass on integrated candidate | Local / test_results.md | Existing unchanged regression suites | Focused 35 tests PASS; original audit FAIL, corrected lock strict audit PASS; full Python 3.12 quality PASS; source/lock frozen byte-equivalent | VERIFIED |
| R461-16 | Map acceptance IDs to meaningful tests/redacted evidence and follow repository completion policy | Governance / six-file package | acceptance_checklist.md and this matrix | Completion audit required; issue stays BLOCKED | PARTIAL |
| R461-17 | Thin entrypoints, application/port reuse, Linux execution; Windows preparation explicitly in scope | Architecture / existing entrypoints | Narrow existing Windows persistence fix; Python boundaries unchanged | Static scope check | VERIFIED |
| R461-18 | Cover plan/apply consent, preservation, rerun, bounded failure and write-free preflight/dry-run | Live and local / existing regression tests, per-run evidence | S02/S03/S08/S09/S10/S13 | Local regressions cannot replace live observations | BLOCKED |
| R461-19 | Avoid duplicating #427, DNS, K3s, Podman or multi-host provisioning | Scope / existing evidence | New bootstrap stages and exact release scenarios only | Static scope check | VERIFIED |

Required live acceptance remains unverified. Actual native exit-2 results are
recorded separately from absent executions; no release is qualified.

## Operator steering and qualification blocker remediation

On 2026-10-10 the operator identified the native SSH and local WSL targets,
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

| R461-22 | Repair the live-observed durable checkpoint replacement failure so reruns/recovery retain confirmed effect evidence | Live blocker remediation / Adapters.ps1 and prepare-windows.Tests.ps1 | Narrow NullString fix; existing atomic replace and ACL guards retained | Windows PowerShell 5.1 isolated actual writer creates pending but effect replacement raises ArgumentException; direct NullString replacement succeeds; canonical pending state unchanged. Real-filesystem regression fails before fix, passes after fix under pwsh7 and WindowsPowerShell5.1; corrected full Python3.12 quality PASS. Corrected live execution pending. | PARTIAL |
