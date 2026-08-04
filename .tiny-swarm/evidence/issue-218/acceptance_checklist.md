# Issue #218 — Final acceptance checklist

Date: 2026-08-04
Rule: every row has exactly one final state. `FAIL` means the requirement is
not fully proven and prevents closure. No row is marked complete merely from a
commit or PR description.

| Requirement | Final state | Evidence / reason |
|---|---|---|
| FR-1 host classification | PASS | Real WSL2 plus automated native/WSL1/unsupported coverage |
| FR-2 filesystem policy | PASS | Real `/mnt/d` block and explicit override evidence |
| FR-3 resource inspection | PASS | Real resource/cgroup/disk collection and tests |
| FR-4 profile assessment | PASS | Real service-access assessment and profile tests |
| FR-5 mutation gate | PASS | Controlled live 8-GiB cgroup returned `INSUFFICIENT`/`RESOURCE_GATED`; Incus/Docker snapshots unchanged |
| FR-6 memory-pressure diagnostics | PASS | cgroup/stat/event implementation and tests |
| FR-7 WSL/Windows network lifecycle | PASS | Stable patched-bundle reachability, controlled changed-IP reconciliation, idempotent prepare, successful elevated cleanup and foreign-rule preservation all pass; the real restart retained the same address |
| FR-8 no uncontrolled hardcoding | PASS | Boundary and adapter tests |
| FR-9 observable workflows | PASS | Fresh installer progress and typed status evidence |
| FR-10 apply/verify separation | PASS | Separate code paths and live commands |
| FR-11 outer timeouts | PASS | Bounded workflow/process tests and live bounded run |
| FR-12 inner timeouts | PASS | Adapter timeout matrix and full gate |
| FR-13 read-only diagnostics | PASS | Live host verify and bounded diagnostic tests |
| FR-14 native Linux isolation | PASS | Ubuntu 24.04.4 native VM: detection and native prepare/verify/cleanup SUCCESS; 202 targeted tests OK; Windows runner not selected |
| FR-15 structured evidence | PASS | All required evidence files contain current implementation, test, live and cleanup observations without secret values |
| NFR-1 idempotence and stale-target reconciliation | PASS | Stable no-op plus controlled changed-IP reconciliation passed |
| NFR-2 reversible owned cleanup | PASS | Elevated cleanup removed managed resources and preserved foreign legacy tuples |
| NFR-3 verify read-only | PASS | Quiesced strict elevated snapshot remained equal across deployment/platform verify |
| NFR-4 responsibility separation | PASS | Architecture lint/tests and source review |
| NFR-5 infrastructure shell boundary | PASS | Runner/adapter boundary and native tests |
| NFR-6 machine-readable results | PASS | JSON CLI and typed evidence tests |
| AC-1 native Linux path | PASS | Actual Ubuntu native VM selected native_linux and completed prepare/verify/cleanup without Windows tools; 202 targeted tests OK |
| AC-2 real WSL2 preflight/reachability | PASS | WSL2 install, DNS, ports and HTTPS stable-address run |
| AC-3 filesystem override | PASS | Blocked default and recorded override |
| AC-4 8 GiB / 10 GiB resource block | PASS | Live nested-cgroup run measured 8 GiB effective memory and blocked before mutation; snapshots unchanged |
| AC-5 sufficient resource reserve | PASS | Real service-access host passed |
| AC-6 bounded hanging verify | PASS | Timeout/termination/workflow tests and bounded run |
| AC-7 progress and heartbeat | PASS | Fresh installer evidence |
| AC-8 failed verify stops later phase | PASS | Workflow/CLI separation tests |
| AC-9 second prepare and changed-IP reconciliation | PASS | Second prepare was a verified no-op; controlled changed-IP adapter/Pester reconciliation passed and Windows HTTPS remained reachable |
| AC-10 verify no mutation | PASS | Strict elevated snapshot with bridge heartbeat paused showed equal portproxy, firewall, hosts, bridge-state, Incus and Docker state |
| Mandatory unit tests | PASS | Full quality gate and targeted suite |
| Mandatory adapter tests | PASS | Python adapter tests and Pester 43/43 |
| Mandatory integration tests | PASS | Full quality gate and 202 targeted native VM host tests |
| Mandatory regression tests | PASS | Composite quality gate: lint, architecture, typecheck and 1576-test suite (28 skipped; 124.501 seconds); Pester 43/43 |
| Mandatory live tests | PASS | Real WSL2/Incus/Swarm, artifacts, deployment, platform, Windows DNS/HTTPS, second prepare, controlled changed-IP reconciliation, cleanup and strict read-only tests pass; Selenium remains an explicitly opt-in browser prerequisite, while external Windows HTTPS is PASS |
| CLI requirements | PASS | Distinct detect/preflight/prepare/verify/cleanup paths |
| Evidence requirements | PASS | All twelve required files are present |
| Documentation requirements | PASS | User guide, installation, troubleshooting and ADR coverage |
| Requirement review | PASS | Current matrix has no open implementation or live acceptance row |
| Architecture review | PASS | Automated architecture checks; final independent review pending |
| Test and evidence review | PASS | Full quality gate, Pester, live workflows, cleanup and strict read-only evidence are current |
| Network review | PASS | Stable reachability, idempotency, controlled changed-IP reconciliation, cleanup and foreign-rule preservation pass |
| Issue Completion Audit | FAIL | Independent PASS cannot be issued while required rows fail |
| Merge verification | FAIL | No merge attempted |
| Issue closure | FAIL | Issue remains open by design |

## Overall

**INCOMPLETE for release lifecycle only.** All local implementation, test and
live acceptance rows are PASS. SonarCloud, merge-commit verification and issue
closure remain FAIL until the guarded publication lifecycle completes.
