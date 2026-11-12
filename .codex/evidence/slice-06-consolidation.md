# S440-06 prerequisite repair consolidation — 2026-11-11

Baseline c40d87ed81101dd582a112fe8b427d84372f36e2; workflow branch
docs/workflow-issue440-acceptance-20261110. Explicit operator fix request covers
the three recorded preflight blockers. Source implementation by real specialist
s06_recovery_design in isolated fix/issue440-s06-recovery worktree; root owns
integration, workflow scope/context and evidence. No commit or push.

Independent architecture design review accepted a narrow implementation of the
existing ALL_STOPPED_COLD_KERNEL_V1 policy with a reviewed S440-06 scope
amendment; no new ADR. Independent security/DevOps and issue-completion review
by s06_security_review inspected final source diff SHA-256
49a1a612e825227e171fef2ba7996b32564d8978c6bf60340bba2714f0785f50.

Root integrated exactly five source/test files. Registration/switch asset pins
now resolve the module layout; the promoted helper's checked source directory
is established before imports. Separate SealFixtureReturn/ReturnFixture phases
use protected bookmark receipts over fixed read-only empty-resource/worker and
source/machine/boot observations. Socket mode validation permits the normal
root-owned group-access socket and binds each response to the verified root
daemon PID via SO_PEERCRED. Inventory collections are deterministic and retain
full resource content. Positively absent daemon state is separate from an
unknown or stopped populated daemon. No fixture return deletes resources.

Read-only FixtureBoundary/FixtureOriginalBoundary observations preserve the
stopped/running original archive, descriptor, transaction absence, registration,
full routes, firewall, hosts and payload. The fixture window never calls Bind or
StageRestore. ReturnOriginal retains its original four product stages. Existing
ResumeOriginal permits the independently reviewed no-transaction original-stopped
return, including only existing owned destination refresh after original IP change.

Regression cases cover empty-resource/worker refusal, deterministic inventory,
checked helper loader and moved assets, fixture return from new_running/safe/
prepared and early prefixes, failed preparation, stale seals and Windows drift,
applied-lost phase observations, unknown reset refusal and product-path exclusion.
The mock-only NEW_NOT_STARTED exception binds the exact seal and captured
original boot; it does not weaken production reset checks.

Initial static audit before authorized verification: **INCOMPLETE**. No unresolved concrete unsafe source
defect was found in the reviewed diff. Tests, full quality, designated-host and
live restoration/listener qualification are **NOT_RUN**. Added tests and source
review are not executed acceptance. Existing S440-05 PASS is not reused.

Known retained pending limits: unknown original-direction reset outcomes,
unapplied/uncertain bridge stop, bound/product intents and ambiguous bridge/runtime
restoration require separate observation/reconciliation, retaining durable intent.
No universal automatic interruption recovery is claimed. No host/bridge/listener
mutation, exact scenario GO, capability admission or parent #440 completion.

Final integrated file SHA-256:

- guest_switch.ps1: e42834dbdb7eef4c292074c932a724a10c65798373606f04583d40009a4f962b
- bridge_binding.ps1: c535d3b4f576f4ddca248c316c30328e94cb5ee7bfc8a5adb03fcf4d46f011a9
- registration.ps1: 2c9fbe29da139eb8e489d6b818104eb9e016bedd21fc49223c94c89c2b85bcbc
- test_wsl_acceptance_guest_switch.py: 9403a59164cc6c3429caf423ca55bc6559ad18859f20ba4b90ac23b1fe86b262
- fixture wsl_acceptance_guest_switch.ps1: b423c4900b81750a52af03f2e46440a6f015cda18d8105dc318bf3989067dbde

## Authorized verification and late delta

The operator subsequently explicitly authorized targeted tests and full quality;
live host switching and infrastructure effects remain excluded. Exact source
manifest: 1811 entries, zero mismatches; Python 3.12.15 in a separately installed
checkout at /home/pc/tsw-440-slice-06-20261111 on designated SSH PC Ubuntu WSL.

Initial targeted run found one real false-readiness defect: Prepare set
PREPARED_READ_ONLY before FixtureEvidence could fail. The two-line correction
moves success after validation. Independent security delta review ACCEPTED guest
switch e42834dbdb7eef4c292074c932a724a10c65798373606f04583d40009a4f962b;
source resynchronized exactly. Targeted retry: 18 PASS, zero skips, 28.459s.
The actual native PowerShell mocked coordinator and registration contracts ran.

Full quality PASS: verification-policy, complexity415, lint, 7 import contracts,
44 architecture tests, 1055-file typecheck; 4058 tests, 37 declared skips, zero
failures/errors in345.937s, exit0. Logs and their hashes are retained under
.tiny-swarm/evidence/issue-440/slice-06/. These are this repair's results, not
reused S440-05 evidence. Final changes only refresh workflow/evidence metadata;
no runtime/test source changed after the passing gate. Exact-source Sonar,
native/WSL live listener/restoration qualification and scenario GO remain open.

## CP_RECORD

- Slice-ID: S440-06
- workflowVersion: 1.0
- Checkpoint: publish the independently reviewed prerequisite repair only.
- Changed files: the five source/test files listed above; workflow.md,
  context-pack.md, context-pack.json, prerequisite-ledger.md and the S440-06
  distribution/consolidation records.
- Targeted command: `PYTHONPATH=. python3 -m unittest modules.tsw_windows_wsl.tests.tools.test_wsl_acceptance_guest_switch modules.tsw_windows_wsl.tests.tools.test_wsl_acceptance_registration -v` — PASS, 18 tests, zero skips.
- Quality command: `python3 modules/tsw_core/tools/linux/quality_gate.py quality` — PASS, 4058 tests, 37 declared skips.
- Verification target: designated SSH PC, Ubuntu WSL; source and retained log
  hashes reobserved unchanged on 2026-11-12. No new test run claimed.
- Rollback reference: c40d87ed81101dd582a112fe8b427d84372f36e2.
- arc42Updated: false; reviewed existing cold-handoff and restoration policy.
- adrUpdated: false; no new architecture decision required for this repair.
- Publication: explicitly authorized by the operator on 2026-11-12; checkpoint
  commit and branch push only, no PR, merge or parent completion claim.
