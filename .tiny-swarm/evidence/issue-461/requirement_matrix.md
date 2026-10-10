# BOOT-W09 requirement matrix

Issue: [#461](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/461).
Candidate: `0528aac913c37ddfd66fc8f326d5f92505bdd7dd`.
Dependencies #459 and #460 are CLOSED and integrated. Status: BLOCKED pending
explicit recoverable-target authorization and remaining target/version facts.
This matrix precedes implementation; no product behavior is changed.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-01 | Define native Ubuntu 24.04/26.04 x86_64 and Windows 11 + Ubuntu WSL2 matrix with exact Windows/WSL versions | Qualification / qualification_matrix.md | Four release rows and required version fields | Read-only N26/W26 version observation; 24.04 targets absent | PARTIAL |
| R461-02 | Run clean-host preparation and install on both families | Live / per-run evidence | S01 in qualification matrix | Not run; LIVE_CONSENT_MISSING | BLOCKED |
| R461-03 | Run repeated preparation and install | Live / per-run evidence | S02 | Not run; LIVE_CONSENT_MISSING | BLOCKED |
| R461-04 | Preserve unrelated Incus and WSL resources | Live / per-run evidence | S03 | Not run; LIVE_CONSENT_MISSING | BLOCKED |
| R461-05 | Exercise resource limits with #440/#444 selection semantics | Live / per-run evidence | S04 | Not run; target capacity/selection absent | BLOCKED |
| R461-06 | Cover reboot, selected WSL restart and group refresh | Live / per-run evidence | S05/S06 | Not run; LIVE_CONSENT_MISSING | BLOCKED |
| R461-07 | Cover IP drift and port collision | Live / per-run evidence | S07/S08 | Not run; LIVE_CONSENT_MISSING | BLOCKED |
| R461-08 | Cover unavailable downloads and interrupted-run recovery | Live / per-run evidence | S09/S10 | Not run; LIVE_CONSENT_MISSING | BLOCKED |
| R461-09 | Verify routes and service authentication | Live / per-run evidence | S11 | Not run; credentials/service target unavailable | BLOCKED |
| R461-10 | Record exact committed SHA, host/tool versions, commands, exits and redacted evidence on authorized restorable targets | Evidence / per-run package | Run record contract in qualification matrix | No W09 live record exists | BLOCKED |
| R461-11 | Reuse #363 only with exact scenario/source applicability; reject dirty/mock qualification | Evidence / applicability review | Historical applicability section | #363 source/scenario differ; no live pass inherited | VERIFIED |
| R461-12 | AC1: Both families have fresh/rerun/recovery results with PASS/PARTIAL/BLOCKED | Acceptance / qualification matrix | Explicit BLOCKED rows | No executed live results | BLOCKED |
| R461-13 | AC2: Ordinary WSL preservation and separately explicit reset isolation have real evidence | Acceptance / per-run evidence | S03/S12 | Neither authorized nor executed | BLOCKED |
| R461-14 | AC3: Each supported release qualified or explicitly unsupported/unqualified | Acceptance / qualification matrix | Four UNQUALIFIED rows; excluded target families | Static release classification | VERIFIED |
| R461-15 | AC4: Targeted regressions and applicable quality/security gates pass on integrated candidate | Local / test_results.md | Existing unchanged regression suites | Focused 35 tests PASS; original audit FAIL, corrected lock strict audit PASS; full Python 3.12 quality PASS | BLOCKED |
| R461-16 | Map acceptance IDs to meaningful tests/redacted evidence and follow repository completion policy | Governance / six-file package | acceptance_checklist.md and this matrix | Completion audit required; issue stays BLOCKED | PARTIAL |
| R461-17 | Thin entrypoints, application/port reuse, Linux execution; Windows preparation explicitly in scope | Architecture / existing entrypoints | No product edits | Static scope check | VERIFIED |
| R461-18 | Cover plan/apply consent, preservation, rerun, bounded failure and write-free preflight/dry-run | Live and local / existing regression tests, per-run evidence | S02/S03/S08/S09/S10/S13 | Local regressions cannot replace live observations | BLOCKED |
| R461-19 | Avoid duplicating #427, DNS, K3s, Podman or multi-host provisioning | Scope / existing evidence | New bootstrap stages and exact release scenarios only | Static scope check | VERIFIED |

Every live row remains unverified until an authorized run produces its own
observations and redacted evidence. BLOCKED is a pre-execution state here,
never an executed failed result or release qualification.

## Operator steering and qualification blocker remediation

On 2026-10-10 the operator identified the native SSH and local WSL targets,
then authorized tests directly on native Linux and creation of a Hyper-V
Windows test environment. No destructive reset authorization or native clean
snapshot was supplied. Live state must now distinguish granted test scope
from missing recovery/cleanliness prerequisites.

| ID | Requirement | Type / likely files | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| R461-20 | Remediate observed runtime dependency audit blocker for AC4 without weakening audit | Dependency / requirements.lock | Narrow urllib3 update using Python 3.12 lock generation | New strict audit PASS and full Python 3.12 gate PASS | VERIFIED |
| R461-21 | Use the supplied native target for authorized testing and provision isolated Hyper-V Windows target | Operator scope / protected local VM assets and run evidence | Read-only native inventory; administrator Hyper-V probe prepared | Native freshness/recovery and Windows administrator/media prerequisites pending | PARTIAL |

Declared additional write scope: requirements.lock for the AC4 security
remediation only; protected ignored VM preparation assets/evidence. Product
Python, architecture and bootstrap contracts remain unchanged. A runtime lock
change requires a new committed candidate before qualification. No live mutation
may bypass the requirement for a recoverable target.
