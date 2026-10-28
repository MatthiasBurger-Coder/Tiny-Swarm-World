# S449-02C consolidation — fail-closed Incus qualification runner

Date: 2026-10-28
Workflow: `issue-449-lcm-w09`
Slice: S449-02C — Harden the opt-in live fixture runner before use
Branch: `feature/lcm-w09-issue449-implementation-20261027`
S02C evidence-refresh base HEAD: `a286b22db8988e2cc8fab39d97d6abb34f4129ab` (clean before these evidence-only edits)
Runner/test implementation commit: `01717f6f8e3db5d11633132063625f0471ff8ae9`

## Exact candidate bindings

- Workflow Markdown SHA-256: `bd1da9a53259d3e5c594feaf7738a65f4b750d2a36dc97b8bc489d800a4880b6`
- Context Markdown SHA-256: `04e0b26e1bc94acb5dd771275d64a87d8fb3f751781fff9bf9178b44eb8aa790`
- Context JSON SHA-256: `aed26b1e4eb36571eea25a8f313b7a1f4fab841a07d2dc5d69afc287c33f2ecb`
- Runner SHA-256: `7929f9dc5d6fea32c55125c3b9f8fb4f02b72a07d3ea0ef80cb0a2aea6279c12`
- Tests SHA-256: `6f888dc59182c7b02ed86fd3e80ddbadb5d7e5a6286e27b4c67d5d3eeb7fcba3`
- The context JSON `workflow_artifacts_sha256` binds the exact current workflow and context Markdown hashes above.

The runner executes the supported `incus version` text command and strictly parses exactly ordered Client/Server version lines. It fails closed on malformed output, then checks the pinned server-version observation. This fixes native Incus 6.0.5 rejecting the unsupported `--format json` option; the observed version is not a claim that 6.0.5 supports the new profile capability.

The candidate opt-in project-inventory capture validates target identity and the local Incus Unix endpoint before enumeration; requires the local admin/full-visibility gate; uses fixed read-only argv and strict schemas; applies bounded timeout/output/entity limits; and writes only one sanitized private ext4 artifact. It does not read or create GO, reservation, `NOT_RUN`, or fixture-result state. Project inventory is read-only across all projects; fixture mutations, when separately approved in S449-02, remain scoped to Incus project `default`. Shared profiles, Windows firewall and PortProxy are not modified.

Private runner evidence requires a Linux/WSL ext4 checkout, directory mode 0700 and file mode 0600. The runner rejects DrvFS/NTFS, malformed mount data and ambiguous mount entries before capture commands, GO reads or reservation/result creation. Integration tests verify refusal precedes target commands and evidence creation.

## Reviews and execution boundary

- Four-role workflow/context review decisions for this exact tuple are recorded in the private PC WSL ext4 approval record (directory 0700, file 0600). Host-phase execution requires an `EXECUTION_PLAN` bound to this same tuple; the prior plan against earlier hashes does not apply.
- The S449-02C distribution/consolidation evidence was stale and is being rebound to this candidate; a previous `EXECUTION_PLAN` belonged to earlier workflow/context hashes and does not authorize this revision.
- S449-02C remains a code/test-only slice. No native or WSL host inventory, route capture, fixture, GO, service stop, Incus write, installation or upgrade was performed as part of this slice.

## Verification evidence

Target: `pc@192.168.178.58`, WSL ext4 checkout `/home/pc/projects/issue449-s02c-v132-clean-20261028`. Focused command:

`PYTHONPATH=src /home/pc/.local/state/issue449-s02c-v132/venv312/bin/python -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture`

Focused result: PASS, 95 tests. The runner/test bytes match the hashes above. The test checkout's base HEAD was `be2e031e8f0fb137ea6c15f74d81a88181aa4183` with the exact runner/test files overlaid; it is not represented as a clean checkout at current candidate HEAD.

Full QUALITY result: PASS, exit 0; 43 architecture tests, 2,969 total tests, 18 skipped. It ran on Python 3.14.4 with repository CI-pinned tools in a private venv; log SHA-256 `daa2d3952b97aef496035ea773ede718fa5e79e61df1f832c9761ab15126e8df`, file mode 0600, parent mode 0700. The gate was run before commit `01717f6`, against base HEAD `be2e031` with exact runner/test bytes. The candidate commits contain those same source/test hashes. No post-commit rerun and no CI Python 3.12 result are claimed.

Available native and WSL project-inventory/route artifacts identify source HEAD `be2e031e8f0fb137ea6c15f74d81a88181aa4183`, older than the workflow branch baseline `a286b22`; they are not current-candidate pre-GO evidence. The WSL full ActiveStore route capture returned `JIT_COMMAND_FAILED`. Native current host observations meet R449-33 numerical 17-GiB/8-CPU/150-GiB floors, but the native service-access preflight is blocked by active `snap.lxd.daemon.service`, and no normalized admission artifact exists. Incus 6.0.5 is observed, not admitted as supported for the new capability.

## Decision and handoff

S449-02C source/test code is implemented and its focused/full gates passed for the exact runner/test bytes. Evidence is reconciled to the workflow tuple; the private ext4 record binds the four current role approvals. No S3D result for this corrected tuple or host qualification/mutation is claimed yet. S449-02 may proceed only after current-hash review/S3D, clean exact-source target checkouts, refreshed full route/inventory captures, normalized resource admission, five-role per-host/per-scenario GO and independent result review. AC1–AC5 and W10 remain open; issue #449 is not complete.
