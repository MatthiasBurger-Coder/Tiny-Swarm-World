# S449-02F4 execution record — v1.40

## Implementation release

Base: `910b5ca792f571c503bf01a53e5a6ce0a363f5ee`, prescribed workflow branch. S3D verified the six-file task-owned authoring overlay; unrelated dirty worktrees are excluded.

All six independent role decisions are `APPROVED`: Requirement, Architecture, Python Automation, Tester, Security and DevOps. Each approval binds the following tuple. The JSON-only correction of the historical F3 execution state was independently rebound before release; no normative proof requirement changed.

- Workflow: `6f071c4dc116ddeaf3108401394b4ace46fd215e86f3e1bcc7e982f32453129a`
- Context Markdown: `8b8ac38640691e684ce6c05649c7eac7c500b3babc2f7a47c1850c783b4692aa`
- Context JSON: `5d46b396640f5497cc93625f70b767bb20bda05a562a0b9436f12ba297f2e6e8`
- Normative design: `6a180fa33e49148c9ebae4b9edca5df0cd648bb314e5488b2c91fa39342963e8`
- Distribution: `fec7f88e84f4cfcf9b6a41698d25a27d8175712c367b417d25d8818d685df70c`
- Workflow index: `357f73c3a9d1aba642d358e7f93dab3f4560adab545c0d8d10f3962c1996da68`

S3D returned `EXECUTION_PLAN`, serial group `[S449-02F4]`, after S449-02F3. No dependency cycle or unknown dependency was introduced. The four declared source/test files are released to one sequential implementation worker. Root retains consolidation and verification ownership. All eleven affected-file locks remain mandatory.

This release authorizes implementation and mocked verification through the approved PC WSL host. It does not authorize native inventory, host mutation, ownership admission, maintenance, transition qualification or issue completion. Any native inventory requires a separate post-commit exact-source plan and host GO.

The six roles independently carried their approvals to the tuple above for one bounded compatibility amendment: the optional environment file may also contain one exact canonical Ubuntu PATH assignment, in the two specified literal forms. All other assignments remain blocked. The context summary was synchronized; no other proof requirement changed. DevOps/S3D carried the existing serial `EXECUTION_PLAN` to these exact hashes before release of the PATH extension.

## Frozen implementation and review

- Runner SHA-256: `0a0f6a5d3f2218093379db0c553a7add0b55a124a2ce164abd132c808815e2d6`
- Proof helper SHA-256: `2ecd07b62118dcccf5089f5d808c32ab3255faa32ba8a7480bede51117322aa3`
- Runner tests SHA-256: `2a98f4357c3c50fd85bb28a5344c759b688c6ecded4e373ad5bb1573fa36ae8a`
- Proof tests SHA-256: `76045793c798601d7d7b8839c7a8be9cf329480ca649dfac5edf06954effdda4`
- Verified test archive SHA-256: `ce13a29d5bb4e2ea0a133f876947a024813f66bc0438cb45841dfaab348cf1e1`

Independent Security and Tester implementation reviews accepted this frozen tuple. The Tester identified an intermediate-directory symlink escape in the first implementation. The worker corrected it using pinned directory descriptors, no-follow component opens and package-device checks; real-filesystem regressions cover the normal tree, parent-symlink escape and cross-device cleanup. Both reviewers then rebound their GO to the corrected hashes above.

## Executed verification

The exact archive and every archived file were SHA-256 verified in the dedicated ext4 checkout on the approved PC WSL host. The corrected focused suite passed **105 tests** in 0.146 seconds. No local or native-host test suite was run.

An earlier archive passed 102 focused tests but its full run failed five existing permission-fixture assertions: the verification wrapper had incorrectly applied umask 077 to the test process, making deliberately insecure fixtures private. That failed run is not a pass. The wrapper now keeps evidence logs private while running the test subprocesses with the normal umask 022; the earlier logs and four source/test files were retained privately on ext4.

The fresh full `python tools/quality_gate.py quality` run passed all seven gates. Architecture tests ran 43 tests; full discovery ran 3,100 tests in 173.182 seconds, with 18 skipped. Skips are not executed passes. Focused log SHA-256: `78515523156926debddc3d774b3a3bb50dc37276a18b5117c53eb24e4e14ffa2`; full quality log SHA-256: `7ab73df176e4249a3687262eb689657b1fe55f5ec464a12319b993c0d12fbd1b`.

No native inventory, identity admission on the live host, host mutation or issue completion is claimed. The earlier F3 diagnostic remains a historical blocked result; only the reviewed and mock-tested fallback implementation is ready for its checkpoint.

## CP_RECORD

- `sliceId`: `S449-02F4`
- `workflowVersion`: `1.40`
- `sliceTitle`: Normalize the verified Snap wrapper and direct LXD child
- `responsibleRole`: Senior Python Automation Developer; root consolidation owner
- `changedFiles`: the eleven declared F4 affected files and locks, including four implementation/test files and seven workflow/evidence files
- `qualityCommands`: focused unittest for both native inventory/provenance modules; full `tools/quality_gate.py quality`, through SSH on approved PC WSL after exact-byte verification; WSL `git diff --check`
- `qualityResult`: `PASS`, 105 focused tests, 3,100 full-discovery tests with 18 skipped, all seven gates passed
- `rollbackReference`: `910b5ca792f571c503bf01a53e5a6ce0a363f5ee`
- `arc42Updated`: `false`, qualification-only correction under the existing trusted-root boundary
- `adrUpdated`: `false`, no new runtime or trust boundary
- `commitSha`: recorded by the checkpoint operator after commit
- `nativeInventory`: `NOT_EXECUTED`, separate post-commit exact-source S3D and host GO required
