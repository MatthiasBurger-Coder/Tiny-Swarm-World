# Issue #218 Requirement Matrix

Authority: GitHub Issue #218 plus the user's requirement that each FR runs as
its own serialized `workflow create` and `workflow execute` lifecycle.

Status vocabulary: `OPEN`, `IN_PROGRESS`, `VERIFIED`, `BLOCKED`, `NOT_RUN`.
Implementation may start only for the FR released by the active workflow.

| ID | Requirement | Type | Owning workflow | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|---|
| PROC-001 | Execute FR-1 through FR-15 serially, each with an isolated workflow-create/execute branch, evidence, quality, PR, checks, and merge before the next FR. | Governance | FR-1..FR-15 | workflow ledger | per-FR PR/evidence | IN_PROGRESS |
| OUT-001 | Keep platform deployment from Incus and Docker Swarm onward host-independent wherever possible; host-specific preparation must stay outside the shared platform/deployment core. | Required outcome / architecture | FR-2 revalidation; owned by FR-7/8/10/14/15 | FR-2 keeps filesystem policy outside shared Incus/Swarm/deployment modules; later cleanup/native isolation remain pending | FR-2 static dependency revalidation plus later native/WSL integration | IN_PROGRESS |
| FR-001 | Reliably distinguish native Linux, WSL1, WSL2, and unsupported hosts from osrelease, proc version, WSL interop, and distro signals; return structured distribution/kernel/interop data; reject WSL1. | Functional / architecture | FR-1 | typed host model, detector port/readers, composed CLI/preflight/installer consumers | classifier, adapter, CLI, integration, targeted and full gates | VERIFIED |
| FR-002 | Under WSL detect Windows-mounted repository paths including `/mnt/c`, `/mnt/d`, `/mnt/e`; block heavy live install by default, recommend a Linux home path, support `--allow-wsl-windows-filesystem`, and record the override. | Functional / safety | FR-2 | released to the FR-2 typed policy/inspector/authorization/evidence slice | path policy, stop-order, override-evidence and full gates | IN_PROGRESS |
| FR-003 | Inspect actual WSL CPU and memory using `nproc`, `free -b`, `/proc/meminfo`, `memory.max`, and `memory.current`; return a structured snapshot and SUPPORTED/WARNINGS/INSUFFICIENT assessment. | Functional / scalability | FR-3 | pending | parser and assessment tests | OPEN |
| FR-004 | Validate selected service profile against centrally configured minimum/recommended CPU, memory, and disk for all named services, dependencies, manager, and optional workers. | Functional / configuration | FR-4 | pending | below/at/above tests | OPEN |
| FR-005 | Before any limit-bearing Incus mutation validate requested limits, visible host capacity, active managed-container limits, overcommit policy, and effective meaning; block unusable limits. | Functional / safety | FR-5 | pending | fake Incus plan tests | OPEN |
| FR-006 | Diagnose memory pressure from current/max/high/events/stat, distinguishing high usage, high pressure, max, OOM, OOM kill, and sustained reclaim/I/O while separating facts, assessment, and confidence. | Functional / diagnostics | FR-6 | pending | memory pressure tests | OPEN |
| FR-007 | Add dedicated WSL network preparation/verification behind ports/adapters for WSL IP, manager/Traefik target, Windows reachability, DNS, HTTPS, Firewall, portproxy drift, idempotent updates, and cleanup. | Functional / architecture | FR-7 | pending | fake Windows and plan tests | OPEN |
| FR-008 | Remove uncontrolled hard-coded WSL/Windows/repository assumptions from generic installation paths; resolve repository dynamically and provide host paths/commands through configuration or host adapters. | Architecture / configuration | FR-8 | pending | static path/command audit | OPEN |
| FR-009 | Make long Python workflows unbuffered and observable with structured start, heartbeat, substep completion, elapsed time, and final status. | Observability / UX | FR-9 | pending | progress/heartbeat tests | OPEN |
| FR-010 | Run deployment apply, deployment verify, and platform verify as distinct steps with individual result/evidence/exit status; never shell-chain long workflows; stop later verify after failure. | Functional / resilience | FR-10 | pending | sequencing tests | OPEN |
| FR-011 | Give every long live workflow a centrally configurable outer timeout and distinct SUCCESS/FAILED/TIMED_OUT/INTERRUPTED/BLOCKED result; default 15m TERM plus 30s KILL. | Resilience | FR-11 | pending | hanging workflow tests | OPEN |
| FR-012 | Bound every HTTP connect/total, DNS, Docker inspection/log, Incus exec, and child process call and terminate children after timeout. | Resilience | FR-12 | pending | timeout/cleanup tests | OPEN |
| FR-013 | Provide configurable no-progress detection and non-invasive read-only hang diagnostics for process, Docker service, CPU, I/O, network, child, and uncollected-exit states. | Diagnostics / observability | FR-13 | pending | parser/classifier tests | OPEN |
| FR-014 | Native Linux must never load or execute WSL/Windows preparation, PowerShell, wsl.exe, netsh, Firewall, hosts-file, or portproxy behavior and must use native adapters. | Architecture / regression | FR-14 | pending | native isolation integration test | OPEN |
| FR-015 | Extend installation evidence with host environment, resources, resource assessment, network readiness, and overrides using the required structured schema. | Evidence | FR-15 | pending | evidence schema/round-trip tests | OPEN |
| NFR-001 | Host preparation is idempotent and creates no duplicate Firewall, portproxy, DNS, hosts, or Incus configuration. | Idempotency | FR-5/FR-7/FR-15 | pending | repeated-run tests | OPEN |
| NFR-002 | Tiny Swarm World-owned Windows/WSL network state is identifiable and reversibly removed by controlled cleanup. | Reversibility | FR-7/FR-15 | pending | cleanup plan tests | OPEN |
| NFR-003 | Verify commands are read-only and never change limits, stacks, proxies, DNS, or Firewall; corrections belong to prepare/apply/repair. | Safety | FR-7/FR-10/FR-14/FR-15 | pending | non-mutation tests | OPEN |
| NFR-004 | New production classes keep detection, inspection, networking, execution, evidence, Incus mutation, and Windows execution responsibilities focused. | Architecture | every FR | FR-1 uses separate value objects, port/service, Linux/WSL readers, detector | 3 import contracts, 18 arch tests, independent FR-1 architecture review | IN_PROGRESS |
| NFR-005 | Shell commands execute only in infrastructure adapters; acceptability decisions remain in domain/application logic. | Architecture | every shell-facing FR | FR-1 classification is pure domain logic; readers remain infrastructure | arch tests/import lint/static review | IN_PROGRESS |
| NFR-006 | New checks return machine-readable typed results, not free-form text alone. | Contract / quality | every FR | FR-1 immutable report and deterministic public JSON payload | schema, CLI, Mypy tests | IN_PROGRESS |
| AC-001 | Native preflight detects native_linux, executes no Windows command, loads no WSL network adapter, and is not blocked by absent wsl.exe. | Acceptance | FR-1/FR-14 | FR-1 native detector/preflight path and mutation sentinels implemented; full isolation remains FR-14 | native simulated integration and no-process/no-file CLI tests | IN_PROGRESS |
| AC-002 | WSL2 preflight detects wsl2, measures resources, evaluates project path, checks Windows reachability separately, and produces a structured report. | Acceptance | FR-1/2/3/7/15 | FR-1 structured WSL2 classification implemented; later resource/path/network fields remain owned by FR-2/3/7/15 | simulated WSL2 integration and real read-only WSL2 CLI | IN_PROGRESS |
| AC-003 | A `/mnt/d` live install blocks without override, recommends `/home/<user>/projects/...`, and records an accepted override. | Acceptance | FR-2/FR-15 | FR-2 workflow owns blocker, recommendation, and protected override decision; FR-15 retains final package | filesystem/evidence/installer/setup tests | IN_PROGRESS |
| AC-004 | An 8 GiB service-access host is insufficient/critical; deployment and a 10 GiB manager limit do not start; measured values are reported. | Acceptance | FR-3/4/5 | pending | insufficient fixture | OPEN |
| AC-005 | At effective configured minimum, assessment succeeds and reports planned limits and remaining reserve. | Acceptance | FR-3/4/5 | pending | minimum fixture | OPEN |
| AC-006 | A hung verify adapter is terminated on timeout, maps to TIMED_OUT with substep identity, and does not start platform verify. | Acceptance | FR-10/11/12 | pending | hanging fake test | OPEN |
| AC-007 | Long deployment visibly emits substep start, heartbeat, substep completion, and final status. | Acceptance | FR-9 | pending | progress tests | OPEN |
| AC-008 | Failed/timed-out deployment verify prevents platform verify and owns a dedicated evidence entry. | Acceptance | FR-10/11/15 | pending | sequencing/evidence tests | OPEN |
| AC-009 | Repeated WSL network preparation creates no duplicates, updates stale target addresses, and preserves HTTPS through service-access.tsw.local. | Acceptance | FR-7 | pending | idempotent/stale/HTTPS fake tests | OPEN |
| AC-010 | Deployment verify leaves Incus limits, Docker stacks, Windows portproxy, Firewall, and DNS unchanged. | Acceptance | FR-7/10/12/14 | pending | non-mutation assertions | OPEN |
| UT-001 | Unit-test native Linux detection. | Test | FR-1 | pure classifier plus reader fixtures | `test_classifies_native_linux_with_typed_host_fields` and `test_reads_native_kernel_and_distribution_signals` | VERIFIED |
| UT-002 | Unit-test WSL1 detection. | Test | FR-1 | explicit `wsl1_unsupported` result | `test_classifies_wsl1_as_explicitly_unsupported` plus installer/OS rejection cases | VERIFIED |
| UT-003 | Unit-test WSL2 detection. | Test | FR-1 | dedicated `wsl2` setup path | `test_classifies_wsl2_with_typed_host_fields` plus detector/CLI/integration cases | VERIFIED |
| UT-004 | Unit-test missing `/proc` files. | Test | FR-1 | reader returns bounded missing facts and classifier fails closed | `test_missing_kernel_files_is_sandbox_unverified` plus detector I/O-error cases | VERIFIED |
| UT-005 | Unit-test missing Windows interop. | Test | FR-1 | interop is independent typed boolean | `test_confirmed_wsl2_without_interop_keeps_host_type` and adapter counterpart | VERIFIED |
| UT-006 | Unit-test `/mnt/c` detection. | Test | FR-2 | released to project-filesystem domain/adapter tests | named unit test | IN_PROGRESS |
| UT-007 | Unit-test `/mnt/d` detection. | Test | FR-2 | released to project-filesystem domain/adapter tests | named unit test | IN_PROGRESS |
| UT-008 | Unit-test `/mnt/e` detection. | Test | FR-2 | released to project-filesystem domain/adapter tests | named unit test | IN_PROGRESS |
| UT-009 | Unit-test native Linux filesystem detection. | Test | FR-2 | released to project-filesystem domain/adapter tests | named unit test | IN_PROGRESS |
| UT-010 | Unit-test resource assessment below minimum. | Test | FR-4 | pending | named unit test | OPEN |
| UT-011 | Unit-test resource assessment at minimum. | Test | FR-4 | pending | named unit test | OPEN |
| UT-012 | Unit-test resource assessment above recommendation. | Test | FR-4 | pending | named unit test | OPEN |
| UT-013 | Unit-test Incus limit larger than WSL capacity. | Test | FR-5 | pending | named unit test | OPEN |
| UT-014 | Unit-test memory pressure without OOM. | Test | FR-6 | pending | named unit test | OPEN |
| UT-015 | Unit-test memory pressure with OOM. | Test | FR-6 | pending | named unit test | OPEN |
| UT-016 | Unit-test timeout mapping to TIMED_OUT. | Test | FR-11/12 | pending | named unit test | OPEN |
| UT-017 | Unit-test that platform verify is not started after deployment verify failure. | Test | FR-10/11 | pending | named unit test | OPEN |
| AT-001 | Adapter-test WindowsCommandRunner with fake processes. | Test | FR-7 | pending | named adapter test | OPEN |
| AT-002 | Adapter-test Incus command parsing without real Incus changes. | Test | FR-5 | pending | named adapter test | OPEN |
| AT-003 | Adapter-test `memory.events` parsing. | Test | FR-6 | pending | named adapter test | OPEN |
| AT-004 | Adapter-test `memory.max = max` parsing. | Test | FR-3/6 | pending | named adapter test | OPEN |
| AT-005 | Adapter-test `free -b` parsing. | Test | FR-3 | pending | named adapter test | OPEN |
| AT-006 | Adapter-test `nproc` parsing. | Test | FR-3 | pending | named adapter test | OPEN |
| AT-007 | Adapter-test WSL IP parsing. | Test | FR-7 | pending | named adapter test | OPEN |
| AT-008 | Adapter-test idempotent network rule planning. | Test | FR-7 | pending | named adapter test | OPEN |
| AT-009 | Adapter-test stale portproxy target detection. | Test | FR-7 | pending | named adapter test | OPEN |
| IT-001 | Add a deterministic native_linux integration path. | Test | FR-1/14/15 | `tests/integration/test_host_platform_paths.py` native composed path | `test_native_linux_simulated_detector_preflight_and_cli_path` | VERIFIED |
| IT-002 | Add a deterministic wsl2_simulated integration path. | Test | FR-1/15 | `tests/integration/test_host_platform_paths.py` WSL2 composed path | `test_wsl2_simulated_detector_preflight_and_cli_path` | VERIFIED |
| IT-003 | Add optional real WSL live test marked `wsl_live`, excluded from normal suite and never claimed when not run. | Test / live | FR-15 | pending | marker/config evidence | OPEN |
| RT-001 | Existing native Linux preflight continues to work. | Regression | FR-1/14/15 | typed detector wired into legacy preflight path | expanded targeted preflight/installer suites and full 1,456-test gate | VERIFIED |
| RT-002 | Existing Incus provider continues to work. | Regression | FR-5/15 | pending | provider tests | OPEN |
| RT-003 | Existing LXC node lifecycle continues to work. | Regression | FR-5/15 | pending | node lifecycle tests | OPEN |
| RT-004 | Existing Docker Swarm bootstrap continues to work. | Regression | FR-5/15 | pending | bootstrap tests | OPEN |
| RT-005 | Existing deployment apply continues to work. | Regression | FR-9/10/15 | pending | deployment tests | OPEN |
| RT-006 | Existing deployment verify continues to work. | Regression | FR-9/10/15 | pending | deployment tests | OPEN |
| RT-007 | Existing platform verify continues to work. | Regression | FR-9/10/14/15 | pending | platform tests | OPEN |
| RT-008 | Existing evidence generation continues to work. | Regression | FR-15 | pending | evidence tests | OPEN |
| CLI-001 | Provide visible `host detect` or proven equivalent. | CLI | FR-1 | early read-only human/JSON CLI path | `test_host_detect_human_output_is_complete_and_read_only`, JSON/exit/no-mutation cases, and real WSL2 runs | VERIFIED |
| CLI-002 | Provide visible `host preflight` or proven equivalent. | CLI | FR-2/3/4 | existing global `--preflight` is the governed equivalent; FR-2 adds ordered filesystem output | CLI/preflight JSON and human tests | IN_PROGRESS |
| CLI-003 | Provide visible `host prepare` or proven equivalent. | CLI / mutating | FR-7 | pending | consent/CLI tests | OPEN |
| CLI-004 | Provide visible `host verify` or proven equivalent. | CLI / read-only | FR-7 | pending | non-mutation CLI tests | OPEN |
| CLI-005 | Support `--live --approve-live --service-profile service-access` for host preflight and preserve explicit consent for mutation. | CLI / safety | FR-7/15 | pending | parser/consent tests | OPEN |
| SEQ-001 | Detect host first. | Runtime ordering | FR-1/15 | installer typed detection precedes Python bootstrap, secret writes, and live work | `test_installer_stops_unsupported_host_before_bootstrap_or_file_writes` | VERIFIED |
| SEQ-002 | Validate host filesystem second. | Runtime ordering | FR-2/15 | released to installer/preflight/setup ordering guards | stop-before-bootstrap and stop-before-phase tests | IN_PROGRESS |
| SEQ-003 | Inspect host resources third. | Runtime ordering | FR-3/15 | pending | setup order test | OPEN |
| SEQ-004 | Validate selected service profile fourth. | Runtime ordering | FR-4/15 | pending | setup order test | OPEN |
| SEQ-005 | Prepare host networking before platform deployment. | Runtime ordering | FR-7/15 | pending | setup order test | OPEN |
| SEQ-006 | Verify host networking before Incus. | Runtime ordering / read-only | FR-7/15 | pending | setup order test | OPEN |
| SEQ-007 | Prepare Incus only after host gates. | Runtime ordering | FR-5/15 | pending | setup order test | OPEN |
| SEQ-008 | Create Swarm nodes only after host gates. | Runtime ordering | FR-5/15 | pending | setup order test | OPEN |
| SEQ-009 | Validate/apply container limits before Swarm bootstrap. | Runtime ordering | FR-5/15 | pending | setup order test | OPEN |
| SEQ-010 | Bootstrap Docker Swarm after limit validation. | Runtime ordering | FR-5/15 | pending | setup order test | OPEN |
| SEQ-011 | Run deployment apply separately. | Runtime ordering | FR-10 | pending | sequencing test | OPEN |
| SEQ-012 | Run deployment verify separately. | Runtime ordering | FR-10 | pending | sequencing test | OPEN |
| SEQ-013 | Run platform verify separately and only after deployment verify succeeds. | Runtime ordering | FR-10 | pending | sequencing test | OPEN |
| SEQ-014 | Finalize evidence last and never continue after BLOCKED/non-success. | Runtime ordering / evidence | FR-15 | pending | sequencing/evidence test | OPEN |
| DOC-001 | Update installation documentation. | Documentation | incremental/FR-15 | pending | doc review | OPEN |
| DOC-002 | Document WSL prerequisites separately. | Documentation | incremental/FR-15 | pending | doc review | OPEN |
| DOC-003 | Document native Linux prerequisites separately. | Documentation | incremental/FR-15 | pending | doc review | OPEN |
| DOC-004 | Document resource requirements and effective threshold formula. | Documentation | FR-4/15 | pending | doc review | OPEN |
| DOC-005 | Document project path recommendation and override. | Documentation | FR-2/15 | released to README, installation, usage, arc42 and ADR status updates | independent documentation review | IN_PROGRESS |
| DOC-006 | Document network model and Windows Service Agent ownership/cleanup. | Documentation | FR-7/15 | pending | doc review | OPEN |
| DOC-007 | Document troubleshooting, timeout, and hang diagnostics. | Documentation | FR-11/13/15 | pending | doc review | OPEN |
| DOC-008 | Document CLI examples and explicitly state WSL2 is a dedicated supported host platform, not native Linux. | Documentation | FR-1/15 | dedicated ADR, synchronized arc42 and usage CLI section | independent architecture/console review | VERIFIED |
| DOD-001 | WSL2 is reliably detected. | Done | FR-1/15 | independent WSL kernel plus distro/interop classification | unit, integration, CLI and actual read-only WSL2 detection | VERIFIED |
| DOD-002 | Native Linux is handled separately. | Done | FR-1/14/15 | dedicated native result/adapter behavior; final whole-repository isolation remains FR-14 | native unit/integration and fail-closed legacy mapping | IN_PROGRESS |
| DOD-003 | Windows-mounted project paths are evaluated. | Done | FR-2/15 | released to FR-2 policy, guards, evidence and tests | acceptance/completion audit | IN_PROGRESS |
| DOD-004 | WSL resources are validated before Incus limits. | Done | FR-3/4/5/15 | pending | acceptance audit | OPEN |
| DOD-005 | Memory pressure uses multiple cgroup signals. | Done | FR-6/15 | pending | acceptance audit | OPEN |
| DOD-006 | Dedicated WSL network preparation exists. | Done | FR-7/15 | pending | acceptance audit | OPEN |
| DOD-007 | Generic installation logic contains no direct Windows commands. | Done | FR-8/15 | pending | static audit | OPEN |
| DOD-008 | Apply/verify output is unbuffered and observable. | Done | FR-9/15 | pending | progress tests | OPEN |
| DOD-009 | Long workflows have outer timeouts. | Done | FR-11/15 | pending | timeout tests | OPEN |
| DOD-010 | Deployment verify and platform verify are separate. | Done | FR-10/15 | pending | sequencing tests | OPEN |
| DOD-011 | Verify performs no infrastructure mutation. | Done | FR-7/10/14/15 | pending | non-mutation tests | OPEN |
| DOD-012 | Unit, adapter, integration, and regression tests pass. | Done / quality | every FR/FR-15 | FR-1 adds all four layers plus bootstrap compatibility tests | 345 targeted and full 1,456-test gate pass; later FR gates pending | IN_PROGRESS |
| DOD-013 | Installation evidence is extended. | Done / evidence | FR-15 | pending | evidence audit | OPEN |
| DOD-014 | Documentation is updated. | Done / docs | incremental/FR-15 | FR-1 ADR/arc42/usage synchronized | FR-1 independent doc review; later FR docs pending | IN_PROGRESS |
| DOD-015 | Initial and final Three Amigos gates pass. | Done / governance | FR-1/FR-15 | initial gate evidence | final gate pending | IN_PROGRESS |
| DOD-016 | CI and Sonar checks pass. | Done / quality | every FR/FR-15 | FR-1 run 29201314415 and both PR #220 checks passed; later FR checks pending | per-FR PR checks | IN_PROGRESS |
| DOD-017 | Required PRs are created and merged only after successful gates. | Done / release | every FR | FR-1 PR #220 merged after green checks; FR-2 lifecycle active | GitHub and cleanup evidence | IN_PROGRESS |
| QG-001 | Phase 10 must run at least `pytest` plus every repository-defined quality command, or record an explicit governed verified-equivalent tooling decision where the repository's authoritative suite uses another runner. | Quality governance | FR-15 | repository currently uses unittest through `tools/quality_gate.py`; final pytest/equivalence decision pending | documented tooling decision plus final command evidence | OPEN |
| FORBID-001 | Do not close the issue by only increasing manager resources. | Forbidden | all | enforced scope | diff/audit | IN_PROGRESS |
| FORBID-002 | Do not hard-code only `/mnt/d` detection. | Forbidden | FR-2/8 | FR-2 requires mountinfo plus generic drive handling and false-prefix tests | tests/static audit | IN_PROGRESS |
| FORBID-003 | Do not disable timeouts. | Forbidden | FR-11/12 | pending | config/tests | OPEN |
| FORBID-004 | Do not merely increase sleep durations. | Forbidden | FR-9/11/12 | pending | diff review | OPEN |
| FORBID-005 | Do not retry hangs without diagnosis. | Forbidden | FR-13 | pending | workflow tests | OPEN |
| FORBID-006 | Do not merge host responsibilities into one WSL utility. | Forbidden / architecture | all | per-FR design | architecture audit | IN_PROGRESS |
| FORBID-007 | Do not execute Windows commands from domain/application code. | Forbidden / architecture | FR-7/8/14 | pending | architecture tests | OPEN |
| FORBID-008 | Do not classify WSL as ordinary Linux. | Forbidden | FR-1/14 | WSL2 has dedicated enum/setup path; WSL1 and ambiguity fail closed | classifier, legacy consumer and integration tests | VERIFIED |
| FORBID-009 | Do not skip native Linux regression tests. | Forbidden / quality | every FR | per-FR gate | test evidence | IN_PROGRESS |
| FORBID-010 | Do not downgrade blockers into log-only warnings. | Forbidden / safety | every FR | typed results | acceptance audit | IN_PROGRESS |
| FORBID-011 | Do not claim live WSL verification without an actual approved run. | Forbidden / evidence | every FR | NOT_RUN evidence | audit | IN_PROGRESS |
| FORBID-012 | Do not leave unresolved production TODOs as completion. | Forbidden / quality | every FR | diff/TODO audit | completion audit | IN_PROGRESS |

## Workflow-phase governance

| ID | Required phase evidence | Owner | Status |
|---|---|---|---|
| GOV-001 | Repository and workflow orientation plus direct occurrence impact map. | FR-1 authoring | VERIFIED |
| GOV-002 | Initial Four-Role Three Amigos gate and dependency validation. | FR-1 authoring | VERIFIED |
| GOV-003 | Before behavior changes, preserve characterization tests and inventories of WSL-as-native handling, hard-coded WSL/Windows/repository assumptions, long workflows without outer timeout, and chained or semantically bundled verify steps. | every affected FR | IN_PROGRESS |
| GOV-004 | Host environment model before networking. | FR-1 | VERIFIED |
| GOV-005 | Resource model. | FR-3/4/5/6 | OPEN |
| GOV-006 | Filesystem policy without automatic move/copy. | FR-2 | IN_PROGRESS |
| GOV-007 | Dedicated WSL network adapter behind the service agent. | FR-7 | OPEN |
| GOV-008 | Harden workflow runner and decouple verifies. | FR-9/10/11/12/13 | OPEN |
| GOV-009 | Integrate required installer ordering and native isolation. | FR-14/15 | OPEN |
| GOV-010 | Complete repository test suite and every verified quality command. | every FR/FR-15 | IN_PROGRESS |
| GOV-011 | Real WSL live verification only when explicitly approved; otherwise simulated paths and NOT_RUN. | FR-15 | OPEN |
| GOV-012 | Final Three Amigos completion gate. | FR-15 | OPEN |
| GOV-013 | Synchronize all named documentation. | incremental/FR-15 | OPEN |
| GOV-014 | Dedicated branch/worktree, logical commits, PR, CI/Sonar remediation, merge, and cleanup. | every FR | IN_PROGRESS |
