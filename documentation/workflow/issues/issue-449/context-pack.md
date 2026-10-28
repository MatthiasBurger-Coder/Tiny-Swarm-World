# Context pack — issue-449-lcm-w09

- Workflow version: 1.32 — 85 focused PC-WSL tests PASS; v1.30 and v1.31 full QUALITY PASS historically; v1.32 Python 3.12.15 full QUALITY PASS (43 architecture tests, 885 source files typechecked, 2,959 tests, 18 skipped (not counted as passes); log SHA-256 247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26; private log path .tiny-swarm/evidence/issue-449/s449-private-20261027/quality-gate-s02c-v132-py312-final5.log); implementation-code review is scoped to runner/tests; v1.32 workflow-hash approvals were pending at submission; current outcome belongs in the private approval record; S3D EXECUTION_PLAN recorded; host admission remains pending.
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
Current runner/test hashes `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` / `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668` passed 85 focused PC-WSL tests. v1.30 full QUALITY PASS (exit 0): 43 architecture tests OK, mypy 885 source files clean, 2,959 tests passed and 18 skipped. Log SHA-256 `cd4bb17cfa202f0435a6eda09524518a4b784014974586b4719321e0438858e7`; private ext4 evidence `.tiny-swarm/evidence/issue-449/s449-private-20261027/quality-gate-s02c-v130-isolated.log`, mode 0600. It used fresh private HOME/XDG on ext4 and private TMPDIR outside the repository; `/tmp/tsw-issue449-qual-v130-20261028/tmp` is tmpfs, not ext4. The v1.29 failure arose under TMPDIR in `/home/pc/.local/state`; its exact test and baseline both pass with otherwise identical files and a fresh `/tmp` TMPDIR. The v1.31 full QUALITY gate passed on the prior 5f candidate (historical). The v1.32 clean-checkpoint full QUALITY PASS on Python 3.12.15: 43 architecture tests, 885 source files typechecked, 2,959 tests, 18 skipped; private log SHA-256 247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26; private log path .tiny-swarm/evidence/issue-449/s449-private-20261027/quality-gate-s02c-v132-py312-final5.log. Mandatory v1.32 workflow-hash reviews and live route-state evidence remain pending; not approved. S3D EXECUTION_PLAN is planning evidence only.
- Incus version support for the new selection-scoped capability remains empty
  until the isolated listener fixture and independent review pass.
- No issue is closed by this workflow baseline.

## Required roles

Senior Requirement Engineer, Senior System Architect, Senior Python Automation
Developer, Senior Tester, Senior Workflow Architect, Security, Senior DevOps
Engineer and independent Issue Completion Auditor. All issue-workflow reviews
must bind the final workflow/context hashes.

The current v1.32 runner SHA-256 `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` and test SHA-256 `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668` passed 85 focused PC-WSL tests. The v1.29 full QUALITY attempt had 1 test failure (preflight error-string expectation), 18 skipped, 43 architecture tests OK and mypy 885 files clean; exact test and baseline comparison pass with a fresh `/tmp` TMPDIR. The v1.30 full gate passed as described above; v1.31 full QUALITY also passed on the prior 5f candidate (historical); v1.32 full QUALITY PASS on Python 3.12.15 (43 architecture tests, 885 source files typechecked, 2,959 tests, 18 skipped (not counted as passes); log SHA-256 247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26; private log path .tiny-swarm/evidence/issue-449/s449-private-20261027/quality-gate-s02c-v132-py312-final5.log). S02C scoped runner/test code reviews recorded; mandatory v1.32 workflow-hash reviews remain pending; root hash verification recorded and post-overlay S3D EXECUTION_PLAN; live route-state evidence and acceptance remain pending.
## Per-scenario resource admission and inventory

Native R449-33/34 selection budgets are 10/6/1 GiB RAM, 2/2/4 CPU and
20/50/10 GiB disk (17 GiB, 8 CPU, 80 GiB total). Native host admission is
max(service-access 15 GiB, selection 17 GiB) = 17 GiB RAM, at least 8 CPU and
150 GiB free disk. Keep the existing default 19 GiB guard unchanged. WSL uses
its official separate 10/8/1 GiB, 2/2/4 CPU, 20/50/10 GiB budget: configured
WSL RAM >= 21 GiB, observed guest RAM >= 19 GiB, CPU >= 8, usable disk >= 150
GiB; Windows physical RAM >= 28 GiB, logical CPU >= 11 and >= 20 GiB storage
remaining after swap growth, while configured guest RAM plus `max(4 GiB, ceil(physical RAM / 4))` must fit physical RAM and 8 guest CPUs plus `max(1, ceil(logical CPUs / 4))` must fit Windows logical CPUs. The accepted Three-Amigos requirement decision defines these thresholds, not a host GO. These remain per-scenario admissions tied to `src/tiny_swarm_world/infrastructure/adapters/host/native_preparation.py`, `documentation/arc42/09_decisions/adr-native-linux-preparation-and-install-lifecycle.adoc`, `documentation/arc42/09_decisions/adr-product-effective-infrastructure-source.adoc`, `documentation/arc42/09_decisions/adr-wsl-capacity-adaptation.adoc` and R449-33/R449-34; they are not host qualification results.

The exact native read-only preflight is `./prepare_linux.sh --preflight
--service-profile service-access`, plus the fixed repository, hash, ext4,
CPU/RAM/disk, Incus-version and host-identity commands in the workflow. WSL
uses `prepare_windows.ps1 -Distro <exact distro> -Preflight -Json
-LinuxCheckout <ext4 ROOT>` and the exact guest resource commands pinned there.
Unknown/failing output stops admission. The candidate includes the project inventory capture CLI and sanitized schema. Exact-source focused and full tests and same-hash code reviews pass; per-host live capture, read-only admission, and scenario GO remain pending. No successful live capture is implied.



The resource admission JSON top-level schema is exactly `schema_version,target_host,platform,scenario_id,captured_at_utc,source_commit,candidate,selection,observed,thresholds,checks,decision,commands`; candidate hashes bind workflow, runner, tests and `infra/config/node-providers/provider_config.yaml`, and decision is `PASS|BLOCKED`. Per-host byte budgets, thresholds, checks and safe command-hash policy are pinned in workflow and JSON. Unknowns force BLOCKED. Inventory JSON top-level schema is exactly `schema_version,target_host,source_commit,projects,command_records`; isolation uses the four feature keys with explicit bool/null values and no default inference. Inventory command records carry argv/exit/byte counts only; each stdout/stderr stream is capped at 2 MiB per command, aggregate command output at 16 MiB, serialized sanitized artifact at 8 MiB, total entities at 10,000 and total commands at 10,000. Cap overflow or unknown/incomplete data blocks capture. GO binds SHA-256 of the sanitized artifact.

For resource and inventory commands, record argv, exit status, and output byte counts. Hash raw stdout only for `git status --short --branch`, `nproc --all`, `free -b`, `df -B1 --output=avail ROOT`, and `incus version --format json`. Keep Windows preflight and Incus project/config output only as sanitized parsed fields; never persist or hash raw stdout/stderr. The new inventory collector hashes only its sanitized artifact. Expanded instance argv is exactly `incus config show <instance> --project <project> --format json --expanded`. Exact argv for expanded instance config is `incus config show <instance> --project <project> --format json --expanded`.

## Verification and execution boundary

Run Python tests and all QUALITY gates only through SSH to the approved PC WSL
test host, from a verified checkout with matching files/hashes. During S449-02C, SSH/SCP is limited to PC WSL exact checkout/hash verification and targeted tests/QUALITY gates; native stays untouched. After exact S02C source/reviews, S02 pre-GO permits only the exact read-only source, resource, route and inventory commands in the workflow on the approved native/PC WSL targets, writing only private ext4 evidence. The v1.32 runner/test pair (`f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628` / `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668`) passed 85 focused PC-WSL tests. v1.30 full QUALITY PASS (exit 0); v1.31 full QUALITY PASS on prior 5f candidate (historical); v1.32 full QUALITY PASS on Python 3.12.15 (43 architecture tests, 885 source files typechecked, 2,959 tests, 18 skipped (not counted as passes); log SHA-256 247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26; private log path .tiny-swarm/evidence/issue-449/s449-private-20261027/quality-gate-s02c-v132-py312-final5.log). Four-role workflow-hash review decisions belong in the private v1.32 approval record; post-overlay S3D EXECUTION_PLAN; live route-state evidence remains pending. Normal fixture run and Incus/profile/instance writes, installs/upgrades, service/system changes or other mutations require fresh five-role per-host GO. After GO, live setup and upgrade scenarios run only on the two designated test machines, serialized by host. Keep Windows networking unchanged and do not enable unapproved routes.

See `context-pack.json` for the SHA-256 pins for authoritative governance,
workflow and private requirement-artifact snapshots.
