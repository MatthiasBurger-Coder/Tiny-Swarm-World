# S352-06 distribution

Workflow: issue-352-configuration-parsing-boundary; workflowVersion 1.0.
Predecessor checkpoint: 4ed53794; declared dependencies: ['S352-05'].
S3_STATUS: clean before slice execution; earlier unrelated Jenkins edits were separately committed as c6685c44. No overlapping changes permitted. S3_BRANCH: architecture/workflow-352-config-parsing-20260925 verified.
S3_SCOPE: exact affected files below; S3_CLASSIFY backend/tests (06 architecture/docs).
S3D: serial acyclic dependency chain; shared contracts/composition/evidence.
Execution mode: sequential; single backend/test writer, root consolidation.
Real subagents: Python implementer and read-only architecture/test reviewers.
Fallback: none. New worktrees: none; user requests branches in existing checkout.
Expected areas: ['configuration']. Frontend/live runtime changes: none.
File locks/allowed product and test writes:
- tests/architecture/test_hexagonal_imports.py
- .importlinter
- documentation/arc42/05_analysis/arch-03-09-configuration-parsing-boundary.md
- documentation/arc42/05_building_blocks.adoc
- documentation/arc42/08_concepts.adoc
- documentation/arc42/08_configuration/operator-configuration-contract.md
- documentation/arc42/08_configuration/config-contract-inventory.md
- documentation/workflow/requirement-matrix.md
- .tiny-swarm/evidence/issue-352/**

Contract locks: ['configuration-validation-contract']; architecture locks: ['configuration-to-core-boundary'].
Parallel writing rejected due to overlapping files and dependent contracts.
Root owns issue/workflow evidence. Existing unrelated files stay untouched.
Required quality: targeted commands below, then full quality and diff check.
- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`
- `git diff --check`
- `python3 tools/quality_gate.py quality`

Consolidation: accept only scope-verified implementation, tests and independent review; record evidence and one slice commit/push. No PR, merge, live infrastructure or cleanup.

Reviewed provenance-scope correction: `documentation/process/skills/audit/skill-registry.json` is locked/allowed solely for the existing 08_concepts.adoc governing hash, following DOC_GOVERNANCE_FAILURE retry1. No skill registry semantics change.
