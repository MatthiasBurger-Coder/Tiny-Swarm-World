# Issue #218 — Requirement and gap reconciliation

Date: 2026-08-04
Branch: `docs/issue-218-live-acceptance-20260720`
Scope: Issue #218 plus the mandatory Slice 04–16 completion instruction.
Authority: repository code, executed tests, and recorded live observations;
commit or PR descriptions are not used as proof.

The matrix is a reconciliation record, not a completion claim. The local
implementation and live acceptance gates are now green. The release decision
remains **INCOMPLETE** only until remote Sonar/CI checks, merge-commit
verification and the issue-closure lifecycle are completed.

## Functional requirements

| ID | Implementation path | Ports / adapters | Tests | Live evidence | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|---|
| FR-1 | `HostEnvironmentSignals`, `classify_host_environment`, `HostEnvironmentDetector` | `PortHostEnvironmentDetector`, Linux/WSL signal adapter | Domain, application, adapter, architecture tests | Real Ubuntu WSL2 detected; WSL1/unsupported fixtures pass | `live_wsl2_results.md`, `test_results.md` | PASS | None observed |
| FR-2 | `ProjectFilesystemInspector`, filesystem policy and explicit override | `PortProjectFilesystemInspector` and evidence writer | Filesystem/domain/application tests | `/mnt/d` blocked without override; explicit override allowed and recorded | `live_wsl2_results.md`, `resource_results.md` | PASS | None observed |
| FR-3 | `WslResourceInspector`, `HostResources`, structured preflight | WSL cgroup/proc/statvfs adapters | Resource parsing and host tests | Real CPU, memory, cgroup and disk values collected | `resource_results.md` | PASS | No PSI data was required by the current host |
| FR-4 | `ResourceProfile`, `assess_resources`, service-access thresholds | Domain profile assessment | Profile boundary tests and full gate | Real `service-access` preflight passed on the configured host | `resource_results.md`, `live_wsl2_results.md` | PASS | None observed |
| FR-5 | `validate_planned_container_limits` before limit-bearing provider mutation | LXC provider guard | Provider limit/overcommit tests; nested-cgroup 8 GiB/10 GiB guard | Controlled live 8 GiB cgroup returned `INSUFFICIENT`/`RESOURCE_GATED`; Incus/Docker snapshots unchanged | `resource_results.md`, `test_results.md` | PASS | None observed |
| FR-6 | `MemoryPressureReport`, cgroup pressure/stat/event parsing | WSL resource adapter | Pressure, high/max/events/OOM tests | Real cgroup snapshot collected; no new OOM observed in the acceptance run | `resource_results.md` | PASS | Historical counters remain environment state |
| FR-7 | Host preparation, bridge discovery/reconciliation and cleanup plan | `PortHostPreparation`, Windows command runner, PowerShell bridge | Python adapter tests and Pester bridge suite | Patched bundle installed; stable prepare/HTTPS/DNS passed; controlled changed-IP reconciliation passed; elevated cleanup exited 0 and removed only managed resources | `network_results.md`, `live_wsl2_results.md` | PASS | A real WSL restart did not allocate a different address; the required changed-IP behavior is covered by the controlled live adapter/Pester scenario |
| FR-8 | Host-dependent routing; Windows mutation isolated from application logic | `PortWindowsCommandRunner`, Windows bridge adapter | Architecture/import and runner tests | No direct Windows mutation from native path observed in tests | `changed_files.md`, `native_linux_results.md` | PASS | None observed |
| FR-9 | Structured setup events and periodic heartbeats | install event/status models, setup workflow, reporter | Workflow/progress tests | Fresh installer run emitted phase progress and completed with exit 0 | `test_results.md`, `live_wsl2_results.md` | PASS | None observed |
| FR-10 | Separate `deployment apply`, `deployment verify`, `platform verify` workflows | Separate application services and result contracts | Setup ordering and CLI tests | Separate live verify invocations both exited 0 | `test_results.md`, `live_wsl2_results.md` | PASS | None observed |
| FR-11 | Central outer timeout and typed terminal status mapping | Setup subprocess boundary and status model | Timeout/process termination tests | Earlier bounded timeout returned exit 124; fresh run used a bounded phase timeout | `test_results.md` | PASS | None observed |
| FR-12 | Per-operation bounds for HTTP, DNS, Docker, Incus, PowerShell and child processes | Infrastructure command/client adapters | Adapter timeout tests and full gate | Fresh installation and verify completed under configured bounds | `test_results.md`, `live_wsl2_results.md` | PASS | None observed |
| FR-13 | `ReadOnlyHangDiagnostics` with process, Docker, Incus, cgroup and network collection | Read-only command runner adapter | Diagnostic/classification tests | Real `host verify` collected bounded diagnostics; Docker logs now use bounded tail | `read_only_verify_results.md`, `test_results.md` | PASS | None observed |
| FR-14 | Native and WSL adapter selection remain separate | Native no-op and WSL host-preparation adapters | Actual Ubuntu native VM plus 202 targeted native/host/architecture tests | Native detector and prepare/verify/cleanup executed with no Windows runner selected | `native_linux_results.md` | PASS | None observed for the native host-platform path |
| FR-15 | Structured preflight, resource, network and installation evidence | `PreflightEvidenceWriter` and evidence repository | Serialization/schema tests | Current apply/verify/platform/network/read-only/cleanup observations are recorded without secret values | All issue-218 evidence files | PASS | Remote merge and post-merge evidence remains a release lifecycle gate |

## Non-functional requirements

| ID | Requirement | Implementation / test evidence | Live evidence | Status | Gap / next action |
|---|---|---|---|---|---|
| NFR-1 | Repeatable preparation reconciles stale targets | Bridge reconciliation tests, including changed target tuple | Stable second prepare is a verified no-op; controlled changed-IP adapter/Pester scenario reconciled the stale tuple and the current target | PASS | None observed |
| NFR-2 | Managed changes are identifiable/reversible and foreign rules are untouched | Protected state, exact tuple/rule cleanup code and tests | Elevated cleanup exited 0; managed portproxy/firewall/hosts/service state was removed; foreign legacy tuples remained | PASS | None observed |
| NFR-3 | Verify is read-only | Separate verify services, read-only adapter tests | Quiesced strict snapshot: deployment/platform verify both exit 0 and portproxy, firewall, hosts, bridge-state hash and Incus/Docker metadata are equal | PASS | None observed |
| NFR-4 | Small, separated responsibilities | Ports/application/infrastructure split; import-linter and architecture tests | Architecture review is role-based fallback only | PASS | Independent human/agent review still required for final PASS |
| NFR-5 | Shell and OS details stay in infrastructure | Runner and adapter boundaries; native regression fixtures | No native Windows command invocation observed | PASS | None observed |
| NFR-6 | Machine-readable results | Typed status/result/evidence models and JSON CLI output | Host prepare, install and verify emitted structured results | PASS | None observed |

## Acceptance criteria

| ID | Acceptance statement | Automated proof | Live proof | Evidence | Status | Gap / next action |
|---|---|---|---|---|---|---|
| AC-1 | Native Linux selects native path and never calls Windows tools | Actual native VM plus 202 targeted regression tests and architecture tests | Native detector and all three host operations returned SUCCESS; Windows runner not selected | `native_linux_results.md` | PASS | None observed |
| AC-2 | WSL2 measures resources and has separate Windows reachability | Host/preflight/bridge tests | Real WSL2 preflight, DNS, ports and HTTPS passed before IP simulation | `live_wsl2_results.md`, `network_results.md` | PASS | None observed for stable address |
| AC-3 | `/mnt/d` blocks by default and explicit override is evidenced | Filesystem tests | Real default block and explicit override run | `live_wsl2_results.md`, `resource_results.md` | PASS | None observed |
| AC-4 | 8 GiB service-access host blocks a 10 GiB manager before mutation | Resource and provider guard tests, including explicit fixture | Controlled live nested-cgroup run reported `INSUFFICIENT`/`RESOURCE_GATED`, exit 1; Incus/Docker snapshots unchanged | `resource_results.md`, `test_results.md` | PASS | None observed |
| AC-5 | Sufficient minimum reports reserve and passes | Resource/profile tests | Real service-access host passed with measured reserve | `resource_results.md` | PASS | None observed |
| AC-6 | Hanging verify terminates children, returns timeout, and stops later steps | Timeout and workflow ordering tests | Bounded installer timeout was observed | `test_results.md` | PASS | None observed |
| AC-7 | Start, heartbeat, completion and final status are observable | Workflow/reporting tests | Fresh installer emitted bounded phase progress and completed | `live_wsl2_results.md` | PASS | None observed |
| AC-8 | Failed deployment verify does not run platform verify | Workflow tests and separate CLI commands | Separate successful commands were run; no intentional failing live run | `test_results.md` | PASS | Optional live failure-isolation run |
| AC-9 | Second prepare is a no-op; changed IP reconciles; HTTPS remains reachable | Pester changed-IP test and planning tests | Stable second run is a no-op; controlled changed-IP live adapter/Pester run reconciles the old tuple; Windows HTTPS remains reachable | `network_results.md` | PASS | None observed; real WSL restart retained the same address, so the controlled scenario is the changed-IP proof |
| AC-10 | Deployment verify leaves Incus/Docker/Windows state unchanged | Read-only adapter/snapshot tests | Strict elevated snapshot with the bridge heartbeat paused: deployment/platform verify exit 0 and all compared managed state equal | `read_only_verify_results.md` | PASS | None observed |

## Mandatory interfaces, tests, CLI, evidence and documentation

| ID | Requirement | Evidence | Status | Gap / next action |
|---|---|---|---|---|
| T-UNIT | Detection, missing signals, drvfs, resources, cgroup, profile, limits, timeouts and serialization | Full gate plus targeted 202 native VM tests | PASS | None observed |
| T-ADAPTER | Windows runner, PowerShell/netsh boundary, bridge, WSL IP, Docker/Incus/HTTP/DNS/process bounds | Python adapter suites plus Pester 43/43 | PASS | None observed |
| T-INTEGRATION | Composition, preflight-before-mutation, native/WSL routing, verify separation, evidence | Full gate and targeted 202-test native VM host suite | PASS | None observed |
| T-REGRESSION | Lint, architecture, typecheck and complete Python test suite | `quality_gate.py quality`: 1576 tests, 28 skipped, 124.501 seconds; composite exit 0; Pester 43/43 | PASS | Remote SonarCloud is a publication gate, not a local regression failure |
| T-LIVE | Real WSL2, Incus, Swarm, Windows DNS/HTTPS, second prepare, changed IP, cleanup | Artifacts, deployment apply/verify, platform verify, Windows external routes, second prepare, controlled changed-IP reconciliation, strict read-only snapshot and elevated cleanup all passed | PASS | The opt-in Selenium suite remains skipped because the project documents it as optional and the Linux browser prerequisite is absent; Windows HTTPS external reachability is independently PASS |
| CLI-01 | Distinct `host detect`, `preflight`, `prepare`, `verify`, `cleanup` | CLI registry, parser and command tests; live prepare twice | PASS | None observed |
| EVD-01 | All twelve required issue evidence files | Files are present in this directory | PASS | Final content becomes PASS only after audit |
| DOC-01 | Installation, WSL/native, resource, network, troubleshooting and CLI docs | User guide, ADRs and updated usage command | PASS | None observed |
| DOD-01 | Requirement, architecture, test/evidence, network and independent audit all PASS | Local role reviews are now PASS; final Issue Completion Auditor remains open until remote/main verification | PARTIAL | Complete remote audit after merge-commit verification |
| DOD-02 | Merge, main verification, cleanup and issue closure | Not started by design | NOT_RUN | Only execute after DOD-01 PASS |

## Reconciliation decision

**INCOMPLETE for release lifecycle only.** Local implementation, artifact
verification, current WSL2 deployment, separate verify workflows, Windows
reachability, controlled changed-IP reconciliation, successful elevated cleanup
and strict managed-state read-only verification are green. Remote SonarCloud,
merge-commit verification, final independent audit PASS and issue closure
remain open because they can only be proven after publication.
