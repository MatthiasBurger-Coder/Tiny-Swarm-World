# S440-04 distribution

Workflow issue-440-final-acceptance v1.0; S440-04 scoped lifecycle integration. S3 branch/ref/status/scope/contract classification and context hashes pass at 5350b1a0. S02/S03 local D8 and remote checkpoints verified. No live GO.

S3D mode: sequential implementation on the checked dedicated workflow worktree. Shared profile runtime/authority/command dispatch and affected callers cannot split into separate writers safely. Real Codex subagent architecture/backend stream (s01_architecture_review); independent requirement/direct-adapter-gap review (s01_requirement_review); root owns tests, consolidation and publication. No fallback. No parallel write streams or additional worktree required for this slice.

Lock scope: workflow S440-04 existing allowed profile service/composition files, infrastructure lxc/profile subtree and listed tests. First implementation is limited to lifecycle.py, profile_setup.py/profile_change.py/profile_completion.py, a narrow profile/command_policy.py helper under the existing subtree, and test_lxc_profile_lifecycle.py. No application-port/schema, capability asset or other slice source changes. Shared documentation/coordination writes remain root-owned.

Architecture decision: accepted R67k explicitly includes direct adapters. A real active installation lease proves lock/intent but does not grant reviewed Incus capability. Existing direct typed mutation and raw mutation=False argv dispatch omit this authority. Use existing repository injection; fail closed on missing/empty/unknown/revoked authority and mismatched live client/server. Keep typed effect commands only and finite raw read grammar. Move hardened Git source reads into a trusted builder; derive actual filter suppressions rather than trusting raw caller flags and prevent optional index writes. Retain checkpoints, socket/lease/budget and legacy paths. Do not admit any production version.

Tests: regression-only RED first, using existing constructor/public methods and a real temporary lease + fake process runner; no new-parameter TypeError mistaken for security RED. Then admitted test-only positive cases, malformed/revoked/mismatched matrix, observer/expired lease, masked writes and preserved read/budget semantics. Root runs existing S04 targeted commands and full canonical gate via SSH PC Ubuntu WSL on byte-verified source. No live/native host effects or Windows config mutation.

Consolidation: independent source/test review, unchanged quality gates, truthful external Sonar status and exact checkpoint scope. Any out-of-scope caller/test dependency is reviewed before edits. No direct worker commit/push/merge; root integrates one slice only.

Reviewed test scope refinement after canonical TEST_FAILURE: two existing Git transports in test_managed_stack_delivery.py and test_profile_observation.py need real typed source/ls-files staging frames. s04_recovery_review ACCEPT. Assertions and production paths stay as reviewed.
