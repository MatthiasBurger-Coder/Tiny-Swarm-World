# Context pack — issue-449-lcm-w09

- Workflow document version: 1.32 (historical approval state; current candidate status is S02C_CANDIDATE_SYNCED). Current runner SHA-256 `7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12`; test SHA-256 `6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3`; 95 focused PASS on approved PC WSL. Full QUALITY PASS, GATE_EXIT=0, on Python 3.14.4 private venv with CI-pinned tools (43 architecture tests, 2,969 total, 18 skipped; log SHA-256 `daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df`, mode 0600, parent mode 0700). This exact candidate was not run on CI Python 3.12. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. The current candidate has no host/scenario GO or normalized admission. Available native and WSL project inventories and route captures are tied to pre-candidate checkout `be2e031e8f0fb137ea6c15f74d81a88181aa4183`; they are not current-candidate evidence for branch HEAD `a286b22db8988e2cc8fab39d97d6abb34f4129ab`. The native route-state PASS digest `fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758` is historical to that checkout. WSL route-state capture returned `JIT_COMMAND_FAILED` and is not a pass. Current native read-only preflight is blocked by active `snap.lxd.daemon.service`; no normalized current-candidate admission exists.  Per-host/per-scenario GO, admission and mutation remain pending.. v1.32’s 85-test and 2,959-test results, log hash `247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26`, approvals and S3D result are historical only.
- Issue: #449, parent EPIC #440, bounded coordination with #318
- Workflow: `documentation/workflow/issues/issue-449/workflow.md`
- Index: `documentation/workflow/workflow.index.md`
- Implementation branch: `feature/lcm-w09-issue449-implementation-20261027`
- Workflow authoring branch: `docs/workflow-lcm-w09-route-baseline-20261027`
- Base: `a0310224946b63e2152ff4086d22a450c3d0f214`
- Existing root #355 workflow/context are preserved and are not selected for #449.

## Scope and operator decision

The user approved a selection-scoped Incus profile and bounded #318 manifest/
optional-stack semantics: Swagger exposure is `published|internal`; schema-v1
state defaults to `published` and direct-Swarm (`swarm`) ownership without
read-time adoption; Portainer-owned stack updates verify endpoint, stack,
ResourceControl and saved-definition identity, disable pruning, and persist
selection only after Swarm convergence. Internal Swagger has no host-published
ports or implicit route. The TSW application route under qualification is
limited to TCP/10001. The user accepted the existing WSL Windows firewall
(`RemoteAddress=Any`) and complete PortProxy state as-is for this run; the
fixture must preserve both snapshots byte-for-byte and adds no external route;
S449-02C captures effective ActiveStore profiles/global settings/rules and all
associated filter types before GO, verifies and records the exact target host
IP, and the independent review binds that read-only capture to the same target
and route-state digest in the GO;
its sole temporary Incus proxy listener is bound to the unique GO-approved
127.0.0.1 fixture port and must be removed after cleanup. A live GO
may bind an exact empty TCP/10001 host-listener and Incus-route baseline; if
present, current routes must be validated and preserved. The fixture does not
attest reachability through other pre-existing Windows forwards. The broad #318
cross-profile Epic stays open and is not completed by this issue.

The user authorized replacing the three owned TSW instances and waived optional
host-baseline backup work. This does not waive the Portainer cold `/data`
archive required by the Portainer-upgrade contract. Live actions still require
exact-source quality, version capability admission, fresh host JIT, per-scenario
same-hash GO and explicit cleanup/recovery.

## Private evidence handling

The parent issue evidence directory has broad inherited NTFS permissions.
Private records belong only in
`.tiny-swarm/evidence/issue-449/s449-private-20261027/`. Only the human-only
S449-01 profile draft, design acceptance, provenance manifest and ACL record
may use a verified restrictive NTFS ACL alternative. Remove inheritance and
allow only the current user, SYSTEM and Administrators; reject broad Users or
Authenticated Users access.

All S02 capture, GO, reservation/NOT_RUN, review and result artifacts, plus the
workflow-release approval record, require a private POSIX directory with mode
0700 and files with mode 0600 on a local Linux/WSL ext4 filesystem. Approved
live checkouts must not reside under `/mnt/c`, `/mnt/d` or DrvFS, and NTFS
ACL-only protection is insufficient. Verify and record filesystem type, mount
target and modes in
`.tiny-swarm/evidence/issue-449/s449-private-20261027/s02-private-posix-verification.md`.
Do not write private evidence if filesystem or permissions are unverifiable.

## Current evidence state

- Existing bounded native/WSL evidence is historical and remains attached to
  its exact source/revision.
- #449 is INCOMPLETE: AC1–AC4 are partial; AC5 and W10 handoff are open.
- WSL Q12/LIVE-4, Q13 attribution, remaining Q16–Q20 variants, R35 attribution,
  full cross-host source/evidence linkage and independent completion audit remain
  open.
- The v1.6 S449-02C route-state digest binds sorted Incus project names and
  project-qualified TCP/10001 routes across all projects. This is a read-only
  inventory expansion; profile reconciliation and fixture mutations remain
  restricted to Incus project `default`. The S02 GO, review, pre-GO captures
  and result are all under the owner-only child directory.
- The v1.7 amendment confined the S449-01 private profile draft and design
  acceptance record to that directory. The v1.8 amendment also confines all
  private S02 route-capture, GO, review and result artifacts there and clarifies
  R67j source provenance: the expected final record is missing, and the older
  record is superseded. Reconstruct a new acceptance only from exact current
  canonical ADR/Q12 hashes and fresh same-hash reviews; never claim recovery of
  the absent bytes. The v1.9 amendment restricts all runner-used S02 evidence
- Historical v1.32 runner/test hashes `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` / `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668` passed 85 focused PC-WSL tests; v1.30, v1.31 and v1.32 gate details above are historical. Current runner SHA-256 `7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12`; test SHA-256 `6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3`; 95 focused PASS on approved PC WSL. Full QUALITY PASS, GATE_EXIT=0, on Python 3.14.4 private venv with CI-pinned tools (43 architecture tests, 2,969 total, 18 skipped; log SHA-256 `daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df`, mode 0600, parent mode 0700). This exact candidate was not run on CI Python 3.12. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. The current candidate has no host/scenario GO or normalized admission. The v1.32 approval record and S3D result do not authorize this candidate.
- Incus version support for the new selection-scoped capability remains empty
  until the isolated listener fixture and independent review pass.
- No issue is closed by this workflow baseline.

## Required roles

Senior Requirement Engineer, Senior System Architect, Senior Python Automation
Developer, Senior Tester, Senior Workflow Architect, Security, Senior DevOps
Engineer and independent Issue Completion Auditor. All issue-workflow reviews
must bind the final workflow/context hashes.

Historical v1.32 runner SHA-256 `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` and test SHA-256 `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668` passed 85 focused PC-WSL tests. The v1.29 full QUALITY attempt had 1 test failure (preflight error-string expectation), 18 skipped, 43 architecture tests OK and mypy 885 files clean; exact test and baseline comparison pass with a fresh `/tmp` TMPDIR. v1.30, v1.31 and v1.32 full-gate details above are historical; the v1.32 result was 43 architecture tests, 885 source files typechecked, 2,959 tests and 18 skipped, with log SHA-256 `247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26`. Its workflow-hash reviews, private approval record and S3D result do not apply to the current candidate. Current candidate evidence and live capture/blocker state are recorded above; S3D outcomes bind exact hashes and phases; resource admission and acceptance remain unproven; The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. The current candidate has no host/scenario GO or normalized admission.
## Per-scenario resource admission and inventory

Native R449-33/34 selection budgets are 10/6/1 GiB RAM, 2/2/4 CPU and
20/50/10 GiB disk (17 GiB, 8 CPU, 80 GiB total). Native host admission is
max(service-access 15 GiB, selection 17 GiB) = 17 GiB RAM, at least 8 CPU and
150 GiB free disk. The 19 GiB default-node guard applies only where that baseline applies; the accepted ADR supports a 17 GiB `TSW_INFRA_ROOT` override for this native host. WSL uses
its official separate 10/8/1 GiB, 2/2/4 CPU, 20/50/10 GiB budget: configured
WSL RAM >= 21 GiB, observed guest RAM >= 19 GiB, CPU >= 8, usable disk >= 150
GiB; Windows physical RAM >= 28 GiB, logical CPU >= 11 and >= 20 GiB storage
remaining after swap growth, while configured guest RAM plus `max(4 GiB, ceil(physical RAM / 4))` must fit physical RAM and 8 guest CPUs plus `max(1, ceil(logical CPUs / 4))` must fit Windows logical CPUs. The accepted Three-Amigos requirement decision defines these thresholds, not a host GO. These remain per-scenario admissions tied to `src/tiny_swarm_world/infrastructure/adapters/host/native_preparation.py`, `documentation/arc42/09_decisions/adr-native-linux-preparation-and-install-lifecycle.adoc`, `documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc`, `documentation/arc42/09_decisions/adr-wsl-capacity-adaptation.adoc` and R449-33/R449-34; they are not host qualification results.

The exact native read-only preflight is `./prepare_linux.sh --preflight
--service-profile service-access`, plus the fixed repository, hash, ext4,
CPU/RAM/disk, Incus-version and host-identity commands in the workflow. WSL
uses `prepare_windows.ps1 -Distro <exact distro> -Preflight -Json
-LinuxCheckout <ext4 ROOT>` and the exact guest resource commands pinned there.
Unknown/failing output stops admission. Available native and WSL project inventories and route captures are from pre-candidate checkout be2e031e8f0fb137ea6c15f74d81a88181aa4183; they are not exact-current-candidate evidence for branch HEAD a286b22. The native route-state PASS digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 is historical to that checkout. WSL route-state capture returned JIT_COMMAND_FAILED and is not a pass. Current native read-only preflight is blocked by active snap.lxd.daemon.service; no normalized current-candidate admission exists. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. Native preflight is blocked by active `snap.lxd.daemon.service`. The pre-candidate native inventory showed only LXD project `default` and three stopped TSW containers (`swarm-manager`, `swarm-worker-1`, `swarm-worker-2`); no stop GO exists. Native observations: 8 CPUs, MemTotal 20,111,052,800 bytes, MemAvailable 15,452,803,072 bytes, free disk 724,140,146,688 bytes, ext4 `/`; `incus version` reports Client/Server 6.0.5. For native R449-33, accepted floors are 18,253,611,008 bytes (17 GiB) RAM, 8 CPUs and 150 GiB free disk; observations meet those numerical floors. The 19 GiB default-node guard does not apply to this selected native budget because the accepted ADR supports a 17 GiB `TSW_INFRA_ROOT` override. MemAvailable is an observation, not a schema threshold. This comparison is not a normalized resource-admission artifact or PASS: active `snap.lxd.daemon.service` blocks read-only `service-access` preflight, and the current exact admission artifact and per-scenario GO are absent. The Incus version observation does not establish capability support. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites.  The current candidate has no host/scenario GO or normalized admission. Read-only admission and per-host/scenario GO remain unproven; no target mutation or host admission is claimed.



The resource admission JSON top-level schema is exactly `schema_version,target_host,platform,scenario_id,captured_at_utc,source_commit,candidate,selection,observed,thresholds,checks,decision,commands`; candidate hashes bind workflow, runner, tests and `infra/config/node-providers/provider_config.yaml`, and decision is `PASS|BLOCKED`. Per-host byte budgets, thresholds, checks and safe command-hash policy are pinned in workflow and JSON. Unknowns force BLOCKED. Inventory JSON top-level schema is exactly `schema_version,target_host,source_commit,projects,command_records`; isolation uses the four feature keys with explicit bool/null values and no default inference. Inventory command records carry argv/exit/byte counts only; each stdout/stderr stream is capped at 2 MiB per command, aggregate command output at 16 MiB, serialized sanitized artifact at 8 MiB, total entities at 10,000 and total commands at 10,000. Cap overflow or unknown/incomplete data blocks capture. GO binds SHA-256 of the sanitized artifact.

For resource and inventory commands, record argv, exit status, and output byte counts. Hash raw stdout only for `git status --short --branch`, `nproc --all`, `free -b`, `df -B1 --output=avail ROOT`, and exact `incus version` text stdout. For `incus version`, parse only the `Client version` and `Server version` fields; the verified native output was 6.0.5 for both. This command does not establish capability support. Keep Windows preflight and Incus project/config output only as sanitized parsed fields; never persist raw stdout/stderr. The new inventory collector hashes only its sanitized artifact. Expanded instance argv is exactly `incus config show <instance> --project <project> --format json --expanded`. Exact argv for expanded instance config is `incus config show <instance> --project <project> --format json --expanded`.

## Verification and execution boundary

Run Python tests and all QUALITY gates only through SSH to the approved PC WSL
test host, from a verified checkout with matching files/hashes. During S449-02C, SSH/SCP is limited to PC WSL exact checkout/hash verification and targeted tests/QUALITY gates; native stays untouched. After exact S02C source/reviews, S02 pre-GO permits only the exact read-only source, resource, route and inventory commands in the workflow on the approved native/PC WSL targets, writing only private ext4 evidence. Current candidate baseline, runner/test hashes, test and gate totals are recorded above. Available native and WSL project inventories and route captures are from pre-candidate checkout be2e031e8f0fb137ea6c15f74d81a88181aa4183; they are not exact-current-candidate evidence for branch HEAD a286b22. The native route-state PASS digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 is historical to that checkout. WSL route-state capture returned JIT_COMMAND_FAILED and is not a pass. Current native read-only preflight is blocked by active snap.lxd.daemon.service; no normalized current-candidate admission exists. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. Pre-candidate native resource observations are recorded above and do not constitute admission; the 19 GiB default-node guard applies only where that baseline applies; native R449-33 uses the accepted 17 GiB `TSW_INFRA_ROOT` override. The v1.32 approval record and post-overlay S3D `EXECUTION_PLAN` are historical. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites.  The current candidate has no host/scenario GO or normalized admission. S3D outcomes bind exact hashes and phases; per-host resource admission and scenario GO remain unproven. Normal fixture run and Incus/profile/instance writes, installs/upgrades, service/system changes or other mutations require fresh same-hash approval and per-host GO. After GO, live setup and upgrade scenarios run only on the two designated test machines, serialized by host. Keep Windows networking unchanged and do not enable unapproved routes.

See `context-pack.json` for the SHA-256 pins for authoritative governance,
workflow and private requirement-artifact snapshots.
