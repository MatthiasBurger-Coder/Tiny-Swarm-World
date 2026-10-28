# Context pack — issue-449-lcm-w09

- Workflow document version: 1.37; status `ACTIVE_FOR_ISSUE_449`. The user authorized completing #449 on the named test hosts. Every slice still requires fresh same-hash reviews and its own S3D `EXECUTION_PLAN`; live host changes still require exact host/scenario admission and GO. S449-02D is committed at `6a687bddab9893d29c081bc8b8cdd0aa489c16ab`; S449-02E is committed at `6c48b1d0ef90ec0316769257e8a821946b2200c8`. S02D runner/test hashes `4d1bef40aa2be3f3f477d33c98db173bf43290cf23a71f33f9937e0fd089221f` / `deb5a79c706b8f277df55e36e040e2ca0c33289a4b7b1debe58a7f260822b1bc`; S02E runner/test hashes `6982861d785cdfa97f4de14e4f7b2cac8cd355eaff7e2478004c2619b1db72fd` / `86e874528a62664c2d2c6c452a733178cb9c0b6d63fc29f1e19a18a7e6ef413b`. On approved PC WSL, S02E focused suite passed 121 tests and full quality gate passed (43 architecture tests; 2,995 total, 18 skipped). S02F implementation and PC WSL quality verification are complete under v1.37. The v1.36 read-only attempt returned UNIT_SCHEMA_INVALID, produced no artifact, and made no host changes. No new native capture has run; a separate post-commit S3D plan is required. Its read-only queries must bind to already-active full-access service identities and cannot trigger service/socket activation. Version 1.36 reconciles project used_by membership without treating storage pools as project consumers, checks pool-level profile/instance disk reciprocity, includes exact storage-volume list/show argv, and blocks inherited/shared volume owner mismatches at both list and detail stages. The v1.36 S02F attempt contacted only the native test host for a bounded read-only inventory; it returned UNIT_SCHEMA_INVALID and produced no artifact. Native service-access preflight remains blocked by active snap.lxd.daemon.service; the previous WSL route capture failed with JIT_COMMAND_FAILED; no normalized admission or host/scenario GO exists.
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
- Historical v1.32 runner/test hashes `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` / `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668` passed 85 focused PC-WSL tests; v1.30, v1.31 and v1.32 gate details above are historical. Historical runner SHA-256 `7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12`; test SHA-256 `6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3`; 95 focused PASS on approved PC WSL. Full QUALITY PASS, GATE_EXIT=0, on Python 3.14.4 private venv with CI-pinned tools (43 architecture tests, 2,969 total, 18 skipped; log SHA-256 `daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df`, mode 0600, parent mode 0700). This exact candidate was not run on CI Python 3.12. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. The current candidate has no host/scenario GO or normalized admission. The v1.32 approval record and S3D result do not authorize this candidate.
- Incus version support for the new selection-scoped capability remains empty
  until the isolated listener fixture and independent review pass.
- No issue is closed by this workflow baseline.

## Execution-phase amendment v1.35

WSL preflight blocker: the sanitized 509908 result reports Windows optional feature `Microsoft-Windows-Subsystem-Linux` disabled and proposes `enable_features` with Windows restart scope. No feature change or restart occurred. Current read-only S3D does not authorize either. The exact sanitized WSL inventory SHA-256 is `4322d32ecfae2f5e1aae1711b48dbc0cb8007487f8655bc540f80d228c1d9994a`, source commit `50990890330684ef661be7f7ab07b586092641df`, target `192.168.178.58`. S449-02H verifies official applicability. If feature-required/uncertain, require explicit exact Windows-host GO plus restart/recovery evidence; if an applicable Store WSL2 exception is proven, S449-02I must first update `tools/windows/preparation/Policy.ps1`/`Adapters.ps1` with deterministic tests. An unchanged blocked preflight cannot pass.


Current exact-source read-only evidence at commit `50990890330684ef661be7f7ab07b586092641df`: native project inventory `.tiny-swarm/evidence/issue-449/s449-private-20261027/native-issue447-inventory.json` SHA-256 `3898c4a7c16fe93581bafabdd09d7daa11316e375072f288f697e2349b8c45017`; native route-state artifact `.tiny-swarm/evidence/issue-449/s449-private-20261027/native-pre-go-route-state.json` SHA-256 `0af9913c1e997d518b0b62bec0c04ef0d79856ce0267ba338becacfa70e47d8cf`, route digest `4dd67ca44274073ad292e72c2a7cb5f9f36f5c15daf230912f2debb61c8ff91be`. The current WSL project inventory exists at `.tiny-swarm/evidence/issue-449/s449-private-20261027/wsl-issue447-inventory.json`; the exact-source WSL route capture returned generic `JIT_COMMAND_FAILED` and created no route artifact. Older `be2e031e8f0fb137ea6c15f74d81a88181aa4183` artifacts and the earlier native route digest remain historical. These reads are not normalized admission or host/scenario GO.


This is an amendment to the existing issue #449 execution workflow, not a new workflow creation. It adds planned S449-02D (fixture-profile isolation), S449-02E (complete WSL ActiveStore/PortProxy capture with a PowerShell ActiveStore snapshot exception <=120 seconds with stdout <=14 MiB/stderr <=2 MiB; separately captured netsh PortProxy command remains <=30 seconds with <=2 MiB per stream. Both count against shared <=16 MiB aggregate, <=256 commands and <=300-second run limit), S449-02F (read-only native LXD/Incus ownership inventory), conditional S449-02G (native maintenance only after exclusive TSW ownership is proven), conditional S449-02H (WSL feature applicability/maintenance), and conditional S449-02I (narrow Store WSL2 preflight compatibility in the existing Windows PowerShell preparation policy and adapter, with deterministic tests). Route capture stores only safe listener tuples/count/digest; raw `ss` rows, PIDs, process names and paths are redacted. S02D accepts Incus string config values only: limits.cpu and limits.memory use Python 3.12 `re.fullmatch` patterns `[1-9][0-9]*` and `[1-9][0-9]*(KiB|MiB|GiB)?` (official docs: https://docs.python.org/3.12/library/re.html), rejecting trailing newlines; source boot.autostart, if present, is exact lowercase true/false, and derived boot.autostart is always string false for source true/false/absent; no coercion. Persisted Incus TCP/10001 routes use the exact sanitized schema pinned in context-pack.json; complete proxy config stays memory-only, and unknown keys/host paths fail before artifact creation. S02F now explicitly inventories storage volumes, requires root or the matching full-access LXD/Incus socket group, compares list/detail consumer links and resolves reciprocal profile/network/pool/volume ownership. Volume and device configuration remains memory-only; unknown or asymmetric relationships fail closed. This expands only the bounded read-only diagnostic contract; it grants no host mutation. The user authorized issue execution; each newly selected phase still requires fresh same-hash reviews and S3D, and any live host mutation still requires exact host/scenario GO. The historical S449-02 pre-GO S3D plan covers only its original phase. S449-02D and S449-02E are complete; S449-02F remains a bounded read-only native diagnostic slice with its own plan pending. No new host read or mutation is claimed by this metadata update.

The issue acceptance trace remains open: AC1 records current command/runtime/version/timestamp/outcome for every host and transition; AC2 records before/after data, service identity, endpoints and credential-state evidence; AC3 excludes skipped, mocked and login-only checks; AC4 requires cleanup/restoration and explicit unsupported-combination evidence; AC5 maps every parent #440 LCM-01–LCM-05 requirement and W10 handoff to implementation and verification artifacts. AC1–AC4 remain partial; AC5/W10 remain open.

S449-02G is conditional only when exact S449-02F evidence proves the active LXD service owns exactly `swarm-manager`, `swarm-worker-1` and `swarm-worker-2` and no unrelated resources. Otherwise native remains BLOCKED. Its dedicated five-role host/scenario GO must bind exact pre/post state and service/instance identities. Service recovery is verified after restart. A host reboot is a separate host-wide action requiring its own explicit authorization and GO; no reboot is automatic.
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
Unknown/failing output stops admission. Historical be2e031e8f0fb137ea6c15f74d81a88181aa4183 inventory/route captures and native route digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 are not current for 509908. Exact-source 509908 native inventory SHA-256 3898c4a7c16fe93581bafabdd09d7daa11316e375072f288f697e2349b8c45017 and native route artifact SHA-256 0af9913c1e997d518b0b62bec0c04ef0d79856ce0267ba338becacfa70e47d8cf (digest 4dd67ca44274073ad292e72c2a7cb5f9f36f5c15daf230912f2debb61c8ff91be) are exact-source. Exact-source WSL inventory SHA-256 4322d32ecfae2f5e1aae1711b48dbc0cb8007487f8655bc540f80d228c1d9994a at commit 50990890330684ef661be7f7ab07b586092641df; WSL route capture returned JIT_COMMAND_FAILED and created no artifact. Current native read-only preflight is blocked by active snap.lxd.daemon.service; no normalized current admission exists. S3D outcomes are hash-bound and phase-scoped; an `EXECUTION_PLAN` authorizes only its specified phase. Host admission and per-host/per-scenario GO are separate and unproven; no host mutation is claimed. Any later phase requires an `EXECUTION_PLAN` bound to its exact hashes. Native preflight is blocked by active `snap.lxd.daemon.service`. The pre-candidate native inventory showed only LXD project `default` and three stopped TSW containers (`swarm-manager`, `swarm-worker-1`, `swarm-worker-2`); no stop GO exists. Native observations: 8 CPUs, MemTotal 20,111,052,800 bytes, MemAvailable 15,452,803,072 bytes, free disk 724,140,146,688 bytes, ext4 `/`; `incus version` reports Client/Server 6.0.5. For native R449-33, accepted floors are 18,253,611,008 bytes (17 GiB) RAM, 8 CPUs and 150 GiB free disk; observations meet those numerical floors. The 19 GiB default-node guard does not apply to this selected native budget because the accepted ADR supports a 17 GiB `TSW_INFRA_ROOT` override. MemAvailable is an observation, not a schema threshold. This comparison is not a normalized resource-admission artifact or PASS: active `snap.lxd.daemon.service` blocks read-only `service-access` preflight, and the current exact admission artifact and per-scenario GO are absent. The Incus version observation does not establish capability support. The private ext4 approval record at `.tiny-swarm/evidence/issue-449/s449-private-20261027/workflow-execution-approval-current-20261028.md` binds its exact workflow/context hashes and four role decisions; its directory is mode 0700 and file mode 0600. Workflow execution requires all four `APPROVED` decisions and S3D `EXECUTION_PLAN` for the same tuple. Per-host/per-scenario GO and normalized host admission are separate prerequisites.  The current candidate has no host/scenario GO or normalized admission. Read-only admission and per-host/scenario GO remain unproven; no target mutation or host admission is claimed.



The resource admission JSON top-level schema is exactly `schema_version,target_host,platform,scenario_id,captured_at_utc,source_commit,candidate,selection,observed,thresholds,checks,decision,commands`; candidate hashes bind workflow, runner, tests and `infra/config/node-providers/provider_config.yaml`, and decision is `PASS|BLOCKED`. Per-host byte budgets, thresholds, checks and safe command-hash policy are pinned in workflow and JSON. Unknowns force BLOCKED. Inventory JSON top-level schema is exactly `schema_version,target_host,source_commit,projects,command_records`; isolation uses the four feature keys with explicit bool/null values and no default inference. All capture command records use fixed command_id, validated symbolic safe_args, exit status and byte counts only; no argv/path/URL/raw output is persisted. Resource admission may carry stdout_sha256 only for its explicit raw-hash allowlist; route/project inventory does not persist raw hashes; each stdout/stderr stream is capped at 2 MiB per command, aggregate command output at 16 MiB, serialized sanitized artifact at 8 MiB, total entities at 10,000, total commands at 256 and aggregate wall-clock time at 300 seconds. Per-command timeout is 30 seconds except the single PowerShell ActiveStore snapshot at 120 seconds; its separate netsh PortProxy command remains at 30 seconds. Any cap/deadline overflow or unknown/incomplete data blocks capture before artifact creation. GO binds SHA-256 of the sanitized artifact.

For resource and inventory commands, persist fixed command_id, validated symbolic safe_args, exit status and output byte counts; never persist argv, paths, URLs or raw output. Hash raw stdout only for `git status --short --branch`, `nproc --all`, `free -b`, `df -B1 --output=avail ROOT`, and exact `incus version` text stdout. For `incus version`, parse only the `Client version` and `Server version` fields; the verified native output was 6.0.5 for both. This command does not establish capability support. Keep Windows preflight and Incus project/config output only as sanitized parsed fields; never persist raw stdout/stderr. The new inventory collector hashes only its sanitized artifact. Its command records use command_id/safe_args rather than argv and contain no raw output or raw hashes. Expanded instance argv is exactly `incus config show <instance> --project <project> --format json --expanded`. Exact argv for expanded instance config is `incus config show <instance> --project <project> --format json --expanded`.

## Verification and execution boundary

Run Python tests and all QUALITY gates only through SSH to the approved PC WSL test host, from a verified checkout with matching files/hashes. During S449-02C SSH/SCP was limited to PC WSL exact checkout/hash verification and targeted tests/QUALITY gates; native stayed untouched. Current candidate baseline and gate evidence are recorded above. Captures from pre-candidate checkout be2e031e8f0fb137ea6c15f74d81a88181aa4183 are historical. Exact-source 509908 native inventory SHA-256 3898c4a7c16fe93581bafabdd09d7daa11316e375072f288f697e2349b8c45017 and route artifact SHA-256 0af9913c1e997d518b0b62bec0c04ef0d79856ce0267ba338becacfa70e47d8cf (digest 4dd67ca44274073ad292e72c2a7cb5f9f36f5c15daf230912f2debb61c8ff91be) are exact-source observations. Exact-source WSL inventory SHA-256 4322d32ecfae2f5e1aae1711b48dbc0cb8007487f8655bc540f80d228c1d9994a, commit 50990890330684ef661be7f7ab07b586092641df, target 192.168.178.58; exact-source WSL route capture returned JIT_COMMAND_FAILED and created no artifact. The historical native route digest fe31f78643962ce3757e8bcfc8cc8ed1e9c9eb46a2c1728f52f773fbc2f84758 is not current. Current native preflight remains blocked by active snap.lxd.daemon.service; no current normalized admission, host GO or mutation is established. Prior approval/S3D evidence is phase-scoped; no host mutation is claimed.
test host, from a verified checkout with matching files/hashes. During S449-02C, SSH/SCP was limited to PC WSL checkout/hash verification and tests/QUALITY; native stayed untouched. Current candidate baseline is above. Historical be2e031e8f0fb137ea6c15f74d81a88181aa4183 captures are not current. Exact-source 509908 native inventory SHA-256 3898c4a7c16fe93581bafabdd09d7daa11316e375072f288f697e2349b8c45017 and native route artifact SHA-256 0af9913c1e997d518b0b62bec0c04ef0d79856ce0267ba338becacfa70e47d8cf (digest 4dd67ca44274073ad292e72c2a7cb5f9f36f5c15daf230912f2debb61c8ff91be) are exact-source observations. Exact-source WSL inventory SHA-256 4322d32ecfae2f5e1aae1711b48dbc0cb8007487f8655bc540f80d228c1d9994a, commit 50990890330684ef661be7f7ab07b586092641df, target 192.168.178.58. WSL route capture returned JIT_COMMAND_FAILED and created no artifact. Current native preflight remains blocked by active snap.lxd.daemon.service; no normalized admission or host GO exists. Prior approvals/S3D are phase-scoped; no host mutation is claimed.

See `context-pack.json` for the SHA-256 pins for authoritative governance,
workflow and private requirement-artifact snapshots.

## Execution-phase amendment v1.36

S449-02F validates project-level `used_by` against the captured inventory, checks pool `used_by` reciprocity for volume links and direct profile/instance disk-device consumers, and type-checks volume detail `created_at`. Exact `storage volume list` and `storage volume show` argv templates are included. Volumes whose list or detail owner differs from the queried project are explicitly unsupported inherited/shared-volume cases and block capture without an artifact. This remains read-only; no host access is claimed by this amendment.

## Execution-phase amendment v1.37

Three-Amigos contract decision: for only `snap.lxd.daemon.unix.socket` and
`incus.socket`, omitted `MainPID` or explicit decimal `0` normalizes to `0`;
empty, malformed, and nonzero values remain blocked. Only `incus.socket` may
report `loaded/active/running`, and only with its active, stable, allowlisted
`incus.service`, exact allowlisted endpoint and existing rechecks. The first
v1.36 native attempt returned `UNIT_SCHEMA_INVALID`, produced no artifact and
made no host changes. A new read-only capture requires reviews and S3D bound to
the amended source, test, workflow and context hashes. No mutation permission
or host/scenario GO is implied.
Current implementation candidate runner SHA-256: 2084dc090f3b0d55007a9ad017fee4621b4d077642fe402f6fd0538c883f5f0c; test SHA-256: 23c8395a3c8a5b6167f36b5e76f052f9df4a307cdc7499a88c898d0cf942aa37. Focused PC WSL tests passed (53 tests). Full quality passed (3,048 tests, 18 skipped, seven gates, exit 0); log SHA-256 `cc3f5f1b94219e5b4774c57e5f5063b1d8315c497d9938457d9d66c5ed1ec295`. The full gate used isolated HOME `/home/pc/projects/issue449-s02f-home-v137-20261028`. An earlier run under the default HOME failed two Incus preparation tests on a stale checkpoint; the isolated rerun passed. The first focused attempt also exposed an obsolete assertion and is superseded by the passing final 53-test run. No new native capture has run.
