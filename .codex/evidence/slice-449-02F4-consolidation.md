# S449-02F4 execution record

## Current corrective checkpoint — v1.41

Commit `45c56359c9d18b1dd5f2dbdbd8e05fb81c5d646b` contains the original verified implementation below. Its separately approved native S02F capture returned `BLOCKED:SNAP_WRAPPER_UNIT_INVALID`, actual exit 2, with no inventory artifact. The source and the retained F3 private plan were verified unchanged. No runtime mutation occurred; only the approved private evidence-directory ownership and control records were prepared.

A separate, six-role-approved post-commit S3D plan authorized the schema wrapper SHA-256 `aef0b32b50f395ca8126ca0ec878197aa52fcb42396032862f3121ba0f9e87da`. Its three fixed read-only systemctl queries ran once, nonprivileged and with `-B`. Both the normal and `--all` queries omitted only `ExecCondition`, `ExecStartPre`, and `ExecStartPost`; neither had duplicate, unknown or malformed fields, and all five base-field comparisons were true. The wrapper exited 0. This diagnoses serialization only and is not inventory admission.

The v1.41 normative correction permits omission only for those three optional arrays and `EnvironmentFiles`, matching systemd's per-entry array printer. Every other required property remains mandatory; duplicate, unknown and malformed rows and configured execution hooks remain blocked. The original v1.40 evidence below remains historical and receives no credit for unexecuted corrective code or a future native capture.

All six roles approved the corrective tuple below and DevOps/S3D issued `EXECUTION_PLAN` for one serial corrective implementation group on base `45c56359c9d18b1dd5f2dbdbd8e05fb81c5d646b`. The worker changed only the proof helper and its tests under the unchanged eleven-file locks. Independent Security and Tester reviews accepted the exact corrective diff. No native retry is released by this implementation record.

- Corrective workflow: `17df2c3a8f726663e98b4a6b2acaadb78032ea9997f7009ff4324603db6a7002`
- Corrective context Markdown: `25e8fc7f63907f6d76c44a1e791ad6686f2d7b010d2a107ee7adf6af7db98252`
- Corrective context JSON: `a626bc72183b7bf16f8307c8b9b966a3de4babeb272731cf0c259ab93694eae9`
- Corrective normative design: `55accd1fae7cb8b660b053fd4ae3ec927bbc209783a2574cdac172e9256a9bb3`
- Corrective distribution: `fbfcd3c27599d0a23dbb814fe64dc6dc0076e8d6838071e474162279f577bdbc`
- Corrective workflow index: `60218bc626c0f065145951253dfefaac1304f432cbbfffd2b6790af8f68f6274`

The corrective helper SHA-256 is `b656ca13c0a2a00479f7f5abf49cc6337b8b9cff08ed76453cbac1ee1e6979ee`; its test SHA-256 is `242f7047f0dccc975e8c0f782dfb7985446cff595f0485a0fb986eb99783bdb1`. Parent runner and parent tests remain at their original reviewed hashes below. Tests exercise all 16 omission/explicit-empty combinations in both recheck directions, every missing mandatory field, and the unchanged malformed/duplicate/unknown/nonempty-value blockers.

Exact archive `96a32f942720ab92aef42306b281f9c5bfe2b5aa35a97b0c51f17ce16ebbf5ed` and all file bytes were verified on approved PC WSL in the task's ext4 checkout, refreshed to source base `45c56359`. **109 focused tests passed** in 0.128 seconds. Fresh full quality passed all seven gates: 43 architecture tests; 3,104 full-discovery tests in 181.037 seconds, 18 skipped. Skips remain unexecuted. Focused log SHA-256: `8a5659dc4e8acdde3f3e3711ea88c4ff74feec1991fb4b2620abb82da64e4d16`; full log SHA-256: `a0c687c9c9dc08c4ffea5ba3d1884213100dffa77e46960ccafbfa32355e32e6`.

### Current v1.41 CP_RECORD

- `sliceId`: `S449-02F4`
- `workflowVersion`: `1.41`
- `sliceTitle`: Normalize omitted systemd empty-array properties
- `responsibleRole`: Senior Python Automation Developer; root consolidation owner
- `changedFiles`: proof helper and its tests, six declared workflow/authoring documents, this consolidation record
- `qualityCommands`: focused inventory/provenance unittest modules and full `tools/quality_gate.py quality` through SSH on approved PC WSL after exact-byte verification; WSL `git diff --check`
- `qualityResult`: `PASS`, 109 focused tests, 3,104 full-discovery tests with 18 skipped, all seven gates passed
- `rollbackReference`: `45c56359c9d18b1dd5f2dbdbd8e05fb81c5d646b`
- `arc42Updated`: `false`
- `adrUpdated`: `false`, serialization correction only
- `commitSha`: recorded by the checkpoint operator after commit
- `nativeInventory`: previous source attempt blocked; separate post-commit exact-source S3D and host GO required for corrected source

## Original v1.40 implementation release

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

## Original v1.40 CP_RECORD

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
