# BOOT-W10: bootstrap EPIC completion audit

Audit date: 2026-10-17. Issue [#462](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/462),
parent [#452](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/452).
Reviewed baseline: `e5fab1335ef8faf241a49ec7e8ab9aeb3607bab9`.
This is a read-only evidence audit plus operator documentation, not a new live run.

**EPIC closure decision: INCOMPLETE.** Child W01–W09 closure does not establish
all original EPIC acceptance criteria. W09 passed only its explicitly amended
existing-host scope. W10 has no authority to silently extend that amendment to
the original EPIC or claim fresh-host success. The short operator paths are
published with prerequisites and blockers; their clean-host walkthrough acceptance
remains unverified. Do not close #452 on this audit.

## Requirement-to-implementation-to-verification matrix

Paths in the implementation column are under `src/tiny_swarm_world/` unless
otherwise stated. Child evidence is retained under `.tiny-swarm/evidence/issue-N/`;
each named package has `requirement_matrix.md`, `test_results.md` and
`completion_audit.md`. Local passes are historical child results, not new runs.

| EPIC requirement | Child deliverable / implementation | Local verification / evidence | Live disposition |
|---|---|---|---|
| BOOT-01: read-only inventory, plan, readiness and remedies | #453; `prepare_linux.sh`, `prepare_windows.ps1`, `domain/native_preparation.py`, `tools/windows/preparation/Policy.ps1`; bootstrap contract | issue-453 matrix/audit; `tests/test_prepare_linux.py`, `tests/test_prepare_windows.py` | Partial scenario observations in W09; aggregate write-free/preservation coverage deferred |
| BOOT-02: features, distro, systemd and resumable restarts | #456; `tools/windows/preparation/Application.ps1`, `Policy.ps1`, `Adapters.ps1` | issue-456 audit and tests; `tests/test_prepare_windows.py` | Existing WSL restart verified; clean Windows/WSL creation-to-install path unqualified |
| BOOT-03: capacity and preserved configuration | #457; `tools/windows/preparation/Resources.ps1`, `ResourceAdapters.ps1`, `ResourceHost.ps1` | issue-457 matrix/audit; `tests/test_wsl_resource_projection.py` and `tests/windows/resources.Tests.ps1` | Existing allocation/restart observations; full resource-boundary and preservation matrix deferred |
| BOOT-04: clean-host packages/Python on both families | #454; `tools/ubuntu_python_prerequisites.sh`, `application/services/native_preparation.py` | issue-454 audit; `tests/test_ubuntu_bootstrap_integration.py`, `tests/test_prepare_linux.py` | Existing-host Python stage recovery verified; no W09 clean-OS proof |
| BOOT-05: safe Incus initialization/access/resources | #455; `application/services/incus_preparation.py`, `infrastructure/adapters/incus_preparation/` | issue-455 matrix/audit; `tests/test_incus_preparation.py` | Existing resources observed; real stale-to-new group session transition deferred |
| BOOT-06: kernel/network and owned browser routing | #458; `application/services/network_preparation.py`, `infrastructure/adapters/network_preparation/`, existing Windows bridge | issue-458 audit; `tests/test_network_preparation.py`, `tests/test_network_preparation_compatibility.py`, `tests/windows/bridge-preparation.Tests.ps1` | Selected restarts and WSL exposure collision/restoration verified; actual IP drift and browser/Selenium unverified |
| BOOT-07: preparation handoff, preservation and separate reset | #459; `tools/windows/preparation/Handoff.ps1`, `linux-handoff.sh`, `application/services/installation.py`, `simple_installer.py` | issue-459 independent local PASS; `tests/test_install_handoff.py`, `tests/test_simple_installer.py` | Existing Ubuntu26 install/rerun and preservation verified on both supplied hosts; no new-target reset proof transferred; ordinary Windows Apply remains blocked |
| BOOT-08: protected state, recovery and bounded failures | #460; `infrastructure/adapters/bootstrap_state.py`, `tools/windows/preparation/Adapters.ps1` | issue-460 matrix/audit; `tests/test_bootstrap_recovery.py` | Dependency-stage offline/interruption/resume verified; full-entrypoint fault recovery and whole-OS restoration unverified |
| BOOT-09: qualification and copyable instructions | #461 amended evidence; #462 README, installation guide, developer manual and this audit | issue-461 current amended PASS; issue-462 requirement matrix/checks/audit | Existing-host acceptance only; all release rows UNQUALIFIED; original fresh-host walkthrough/EPIC closure criteria open |

## Exact scenario provenance and target versions

Canonical W09 rollup:
[combined qualification](../../.tiny-swarm/evidence/issue-461/combined_qualification_20261017.json),
particularly `latest_campaign`, `scope_amendment_live_deferral_20261017`,
`independent_amended_scope_audit_20261017` and `publication_verification_20261017`.
Read the latest scoped entries before historical failures and superseded decisions.

The final product candidate was `d2fd89be9b2274eeb0c210d140ebee358a1324c4`.
W09 records full install/rerun, selected restart and TLS/API authentication on
existing native and WSL Ubuntu26 targets. Native managed-root recovery used
`4f2e1751` (resolve the full identity in the rollup), while finald2 install/reboot
was separately verified. WSL managed-root snapshot/restore used exactd2. These
source/scenario distinctions must remain; no result is transplanted to current
HEAD, a new host, a plain archive or a clean OS.

| Supplied target | Observed versions | Scope |
|---|---|---|
| N26-SSH-20261017 | Ubuntu 26.04.1 x86_64, kernel 7.0.0-38-generic, systemd, Python 3.14.4, Incus 6.0.5 | Existing installation; scoped LIVE_VERIFIED results; release UNQUALIFIED |
| W26-SSH-20261017 | Windows 11 Pro 10.0.26200.9711, PowerShell 5.1.26100.9711, WSL 3.0.3.0, Ubuntu 26.04.1 x86_64, kernel 6.18.54.1-microsoft-standard-WSL2, Python 3.14.4 | Existing installation; scoped LIVE_VERIFIED results; release UNQUALIFIED |
| Native/WSL Ubuntu 24.04 x86_64 | Implemented candidate support; no W09 live target supplied | UNQUALIFIED; not a W09 amended-scope blocker |

These observations are scenario facts, not a supported-version qualification list.
Windows 10, WSL1, arbitrary distros/releases, ARM and macOS are outside initial
bootstrap scope. Windows policy requires observed WSL >=2.4.10; a minimum version
check alone never qualifies that version. Exact exit codes, source hashes,
failures and recovery results remain in the W09 rollup and linked artifacts.
No browser/Selenium or external SonarQube result is inferred from API tests.

## Remaining closure conditions

1. Clean-host preparation/install walkthroughs on both host families need
   source-bound evidence or an explicit EPIC-level scope decision. W09's deferral
   is recorded, not converted into those passing results.
2. Ordinary Windows Apply is still unqualified-blocked by policy/help. A short
   command and a successful qualification run do not enroll a qualified release.
3. Retained Git metadata is required by current installer secret-ignore checks.
   Windows extracted-release membership proof alone does not make a plain source
   archive a demonstrated end-to-end install path.
4. Actual group-session transition/IP drift, full entrypoint fault recovery,
   broader resource/preservation/read-only cases remain deferred. No whole-OS or
   external-volume restoration claim exists.
5. The local full gate recorded for exactd2 passed 2,631 tests (18 skips), 43
   architecture tests and seven import contracts. It is historical evidence,
   not a newly executed gate for the W10 documentation branch.

No live operation is authorized by this issue. For new qualification, identify a
recoverable target, exact committed source, version inventory, reviewed commands
and fresh consent; preserve redacted exits/evidence. Do not bypass qualification,
source integrity, ownership, reset, credential or capacity guards to complete docs.

## Governance synchronization

The active workflow file concerns completed #355 and grants no #462 product
scope; it is left intact. This isolated branch owns README, installation/developer
instructions, the bootstrap contract status correction and issue-462 evidence.
No architecture, provider, service-selection (#440/#444), ADR decision, quality
threshold, role or runtime ownership changes are introduced. Existing accepted
W07/W08 behavior is documented; historical child evidence remains unchanged.
