# Issue #455 changed files

Task branch: feature/incus-preparation-20261004. Inventory captured before publication. The user subsequently authorized push auto, issue closure and branch cleanup.

- `README.md`
- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/09_architecture_decisions.adoc`
- `documentation/arc42/09_decisions/adr-explicit-incus-preparation.adoc`
- `documentation/contracts/bootstrap.md`
- `documentation/process/skills/audit/skill-registry.json`
- `documentation/system/lxc-native-setup.adoc`
- `documentation/user_guide/installation.adoc`
- `src/tiny_swarm_world/application/ports/incus_preparation.py`
- `src/tiny_swarm_world/application/services/incus_preparation.py`
- `src/tiny_swarm_world/domain/incus_preparation.py`
- `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/__init__.py`
- `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/adapter.py`
- `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/configuration.py`
- `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/preservation.py`
- `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/resources.py`
- `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/runtime.py`
- `src/tiny_swarm_world/infrastructure/adapters/native_preparation_evidence.py`
- `src/tiny_swarm_world/infrastructure/composition_incus_preparation.py`
- `src/tiny_swarm_world/infrastructure/composition_native_preparation.py`
- `src/tiny_swarm_world/prepare_incus.py`
- `src/tiny_swarm_world/prepare_linux.py`
- `tests/architecture/test_architecture_regressions.py`
- `tests/architecture/test_hexagonal_imports.py`
- `tests/test_incus_preparation.py`
- `tests/test_prepare_linux.py`
- `tests/test_ubuntu_bootstrap_integration.py`
- `tests/test_ubuntu_prerequisites.py`
- `tools/ubuntu_python_prerequisites.sh`

Issue evidence (ignored runtime evidence paths explicitly required by governance):

- `.tiny-swarm/evidence/issue-455/acceptance_checklist.md`
- `.tiny-swarm/evidence/issue-455/implementation_summary.md`
- `.tiny-swarm/evidence/issue-455/remaining_risks.md`
- `.tiny-swarm/evidence/issue-455/requirement_matrix.md`
- `.tiny-swarm/evidence/issue-455/test_results.md`
- `.tiny-swarm/evidence/issue-455/changed_files.md`
- `.tiny-swarm/evidence/issue-455/completion_audit.md` (independent final audit, PASS)

README provenance only is refreshed in skill-registry.json; no skill/role/routing
or quality-policy change. Strict architecture allowlists register the new Incus
entrypoint and add its forbidden-adapter mutation test; no cycle exceptions added.
Existing W02 tests mock the separately verified new capability at their boundary.
- `.tiny-swarm/evidence/issue-455/final_completion_report.md`

Publication remediation adds `src/tiny_swarm_world/infrastructure/adapters/incus_preparation/consent.py` (cancellable console boundary).
