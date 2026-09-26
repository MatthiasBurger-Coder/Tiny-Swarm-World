# S352-04 distribution

Workflow: issue-352-configuration-parsing-boundary; workflowVersion 1.0.
Predecessor checkpoint: 8b9d26f9; declared dependencies: ['S352-03'].
S3_STATUS: clean before slice execution; earlier unrelated Jenkins edits were separately committed as c6685c44. No overlapping changes permitted. S3_BRANCH: architecture/workflow-352-config-parsing-20260925 verified.
S3_SCOPE: exact affected files below; S3_CLASSIFY backend/tests (06 architecture/docs).
S3D: serial acyclic dependency chain; shared contracts/composition/evidence.
Execution mode: sequential; single backend/test writer, root consolidation.
Real subagents: Python implementer and read-only architecture/test reviewers.
Fallback: none. New worktrees: none; user requests branches in existing checkout.
Expected areas: ['configuration']. Frontend/live runtime changes: none.
File locks/allowed product and test writes:
- src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py
- src/tiny_swarm_world/application/ports/repositories/port_compose_file_repository.py
- src/tiny_swarm_world/domain/deployment/stack_definition.py
- tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py

Contract locks: ['configuration-validation-contract']; architecture locks: ['configuration-to-core-boundary'].
Parallel writing rejected due to overlapping files and dependent contracts.
Root owns issue/workflow evidence. Existing unrelated files stay untouched.
Required quality: targeted commands below, then full quality and diff check.
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `git diff --check`
- `python3 tools/quality_gate.py quality`

Consolidation: accept only scope-verified implementation, tests and independent review; record evidence and one slice commit/push. No PR, merge, live infrastructure or cleanup.
