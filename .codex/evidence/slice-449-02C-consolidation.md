# S449-02C consolidation — sanitized Incus project-inventory capture

Date: 2026-10-28
Workflow: `issue-449-lcm-w09` v1.32
Slice: S449-02C — Harden the opt-in live fixture runner before use
Branch: `feature/lcm-w09-issue449-implementation-20261027`
Candidate base HEAD: `0cc2bf4c08e5f7eaac6593eb2e380bb2760c6374`
Candidate status: uncommitted; do not treat this worktree as clean or as a released exact-source checkout.

## Exact candidate bindings

- Workflow: `documentation/workflow/issues/issue-449/workflow.md` — SHA-256 `9dc17d3ca7028091d78396fa7d71a53df7f2ca6e59c591d94608e3319102ce5c`
- Context Markdown: `documentation/workflow/issues/issue-449/context-pack.md` — SHA-256 `294d783b43a7140e456bc60231da2c1a53c3278f1f83bed16c3587ce1efabd48`
- Context JSON: `documentation/workflow/issues/issue-449/context-pack.json` — SHA-256 `94c143a8789436180ab477db4aa36a7fe40a90dc34bb91a9ece0eb6de120eda9`
- Runner: `tools/qualification/incus_profile_listener_fixture.py` — SHA-256 `f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628`
- Tests: `tests/infrastructure/adapters/clients/test_lxc_profile_listener_fixture.py` — SHA-256 `8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668`

The context JSON pins the workflow and context Markdown hashes above. Workflow v1.32 separates phases: S02C focused tests run over SSH on PC WSL; later S02 read-only preGO checks run on the two approved hosts; fixture mutations require a fresh per-host GO. Full quality runs only over SSH/SCP on PC WSL. The runner/test hashes and workflow/context pins were verified before the test run.

## Scope and safety behavior

This code-and-test slice hardens the candidate opt-in `--capture-project-inventory` mode. It validates target identity and the local Incus Unix endpoint before enumeration, requires the local admin/full-visibility gate, and does not hash endpoint/admin command output. The mode uses a fixed read-only argv allowlist, strict schemas and type checks, and bounded command, stream, aggregate, entity, timeout, and sanitized-artifact limits. It stores only sanitized inventory plus command metadata in one exclusive private ext4 artifact, and does not read or create GO, result, reservation, or `NOT_RUN` state. The separate `--capture-route-state` mode pre-existed this slice.

Private runner artifacts require a Linux/WSL ext4 checkout and owner-only POSIX modes. The runner resolves the checkout/evidence path against `/proc/self/mountinfo`, rejects `/mnt/c`, `/mnt/d`, non-ext4 filesystems, unreadable or malformed mount data, and conflicting or ambiguous entries at the deepest mountpoint. The guard runs before capture commands and file creation, before GO is read, and before reservation/result creation. Integration tests verify those paths stop without host commands or evidence artifacts when the guard rejects the filesystem.

Incus project inventory is read-only across all projects and project-qualifies any TCP/10001 route. All fixture mutations remain in project `default`; the shared profile is not modified. WSL firewall and PortProxy state are read and compared only. No installation, live Incus operation, external route, firewall change, or PortProxy change was performed in this slice.

## Reviews and workflow gates

- The v1.32 workflow/context hashes are bound above; context JSON must parse and its pins must match before release. Runner/test hashes are unchanged from the current 85-focused PC-WSL test result.
- The four-role workflow release gate is decided by the private approval record for the exact v1.32 workflow/context hashes. Scoped runner/test reviews do not substitute for those approvals.
- S3D returned EXECUTION_PLAN for the exact seven-file tuple (artifact `s3d-preflight.md` (digest recorded in the private review disposition)). This is planning evidence only. No S02 capture, GO, or Incus mutation occurred.
- `git diff --check` passed after the runner/test changes; repeat after final evidence edits.

## Verification on the approved PC WSL test host

Target: `pc@192.168.178.58`, WSL ext4 checkout `/home/pc/projects/issue449-s02c-v132-clean-20261028` at baseline HEAD `0cc2bf4c08e5f7eaac6593eb2e380bb2760c6374` plus the exact seven-file overlay, Python 3.12.15 venv `/home/pc/.local/state/issue449-s02c-v132/venv312`, and private HOME/XDG state. For focused validation, only runner, tests, workflow, and context files were modified in that checkout; their exact hashes were verified.

The runner/test hashes above were verified on the exact clean-checkpoint candidate under Python 3.12.15. Focused command:

`PYTHONPATH=src /home/pc/.local/state/issue449-s02c-v132/venv312/bin/python -m unittest tests.infrastructure.adapters.clients.test_lxc_profile_listener_fixture`

Current focused result: PASS - 85 tests on Python 3.12.15; private log path .tiny-swarm/evidence/issue-449/s449-private-20261027/focused-tests-s02c-v132-py312-final5.log; SHA-256 07062fbb18acd748a11434e6e7fea4958dd7ececd213a9d0ba53e8a6c7e0209d; runner SHA-256 f37ab8fbe98b288b75451b8798607d588b2bef0458f6730cf8af405acc740628; test SHA-256 8168ffbdcf0a5ac816134c23a25de1052f276189f4ab60066ffb7ebeb9e45668. This confirms source/test verification only; no target preGO or state access.

Historical full QUALITY results:

- v1.29: FAIL, 2,959 tests, 1 failure, 18 skipped; the failure was a native-preflight expected/actual message mismatch. Private log: `candidate private quality-gate-s02c-v129-isolated.log`.
- v1.30: PASS; 43 architecture tests OK, mypy 885 clean, 2,959 tests, 18 skipped, exit 0. Log SHA-256: `cd4bb17cfa202f0435a6eda09524518a4b784014974586b4719321e0438858e7`.
- v1.31: PASS on the prior non-clean candidate at HEAD `5f11240`: 2,959 passed, 18 skipped, exit 0. Log SHA-256: `c88a42012cfadf458a647e49072ea6375d1d532a659f649ab5ddf916142e01fb`.

The isolated `TMPDIR` was fresh `/tmp` on tmpfs; the private evidence directory and logs were stored on ext4 with mode 0700/0600. The v1.32 full gate passed on the exact clean checkpoint under Python 3.12.15; its private log path .tiny-swarm/evidence/issue-449/s449-private-20261027/quality-gate-s02c-v132-py312-final5.log, SHA-256 247da0bd35bbf91138811ba7355f39681fd7dc5b3e47c78474cdc4b806a90e26. Mandatory v1.32 workflow-hash approvals remain pending; S3D EXECUTION_PLAN is planning evidence only.

## Decision and handoff

S449-02C has current focused and full QUALITY passes on the exact v1.32 clean checkpoint; Scoped runner/test implementation reviews are recorded; mandatory workflow-hash release reviews remain pending. Root hash verification and S3D EXECUTION_PLAN are recorded. It has not qualified native Linux or WSL2, and it does not authorize S449-02 execution by itself. S449-02 still requires current per-host route captures, issue447 inventory, resource admission, scenario-specific five-role GO, and independent result review. The workflow remains sequential; issue #449 stays open until S449-02 through S449-09, AC1–AC5, W10, and the independent issue-completion audit are complete.
