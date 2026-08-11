# Slice Distribution — I156-S03

Workflow: issue-156-20260809
Workflow version: issue-156-v1.0.0
Slice ID: I156-S03
Slice title: Apply registry ports to core service stacks

## Execution decision

- Serial execution after I156-S02; the user requested issue-by-issue and slice-by-slice progression.
- The workflow marks this slice parallel-eligible with I156-S04, but no parallel worktree is used because the chain is intentionally serialized and the shared Compose repository test file is a lock boundary.
- Streams reviewed: Python infrastructure/Compose, architecture, tests, requirements, DevOps, quality.
- No real subagent tool is visible; explicit role-based fallback review will be recorded.
- Expected product change: regression coverage proving registry-backed rendering for Portainer, Jenkins, SonarQube and Nexus, including optional Nexus Docker ports.
- Existing core Compose values were verified against `infra/config/ports.yaml`; no value-only edits are authorized when the committed definitions already match the registry.
- Live deployment, Docker/Swarm commands and bootstrap actions are out of scope.

## Locks and gates

- File locks: `infra/config/compose/portainer/**`, `infra/config/compose/jenkins/**`, `infra/config/compose/sonarqube/**`, `infra/config/compose/nexus/**`, and the focused Compose repository test.
- Contract locks: `I156-registry-resolution`, `I156-core-published-ports`.
- Architecture lock: internal target ports remain unchanged.
- Targeted gate: `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`.
- Required gate: `python3 tools/quality_gate.py quality` after implementation.

## Role review

- Senior Python Automation Developer: verify central mapping is exercised without duplicating resolver logic.
- Senior System Architect: reject target/published inversion or unnecessary Compose changes.
- Senior Tester: cover all four core stacks and optional Nexus mappings.
- Senior Requirement Engineer: map REQ-156-01, REQ-156-02, REQ-156-07, REQ-156-08 and REQ-156-09 to evidence.
- Senior DevOps Engineer: confirm no live stack mutation and no provider/bootstrap scope.

## Consolidation plan

Use the smallest test-only change if the checked-in Compose values already satisfy the central registry. Review staged files, run focused and full quality gates, create consolidation evidence, then commit exactly I156-S03.
