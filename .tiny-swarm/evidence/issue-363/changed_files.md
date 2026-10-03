# Changed files

- `.tiny-swarm/evidence/issue-363/requirement_matrix.md`: maps all issue
  requirements to evidence and current status.
- `.tiny-swarm/evidence/issue-363/implementation_summary.md`: describes the
  current validation scope and historical-evidence boundary.
- `.tiny-swarm/evidence/issue-363/changed_files.md`: records the scoped change set.
- `.tiny-swarm/evidence/issue-363/test_results.md`: records executed commands.
- `.tiny-swarm/evidence/issue-363/remaining_risks.md`: records live blockers.
- `.tiny-swarm/evidence/issue-363/acceptance_checklist.md`: tracks acceptance.
- `.tiny-swarm/evidence/issue-363/three_amigos.md`: records review perspectives.
- `.tiny-swarm/evidence/issue-363/completion_audit.md`: records the independent
  INCOMPLETE completion decision and its open requirements.
- `tools/live/run_classic_acceptance.py`: classifies setup preflight resource
  gates as blocked before mutation when its structured result proves that state.
- `tests/tools/test_classic_live_runner.py`: regresses the observed failure
  classification while retaining later-phase failure behavior.
- `documentation/evidence/wsl2-secure-live-path.md`: documents the corrected
  preflight live state.
- `src/tiny_swarm_world/domain/preflight/resources.py` and
  `src/tiny_swarm_world/infrastructure/composition_runtime.py`: select the
  existing WSL2 16 GiB service-access minimum while keeping native Linux at
  20 GiB.
- `tests/domain/preflight/test_resources.py` and
  `tests/infrastructure/test_composition.py`: pin both host thresholds.
- `documentation/user_guide/installation.adoc`: records the two host limits.
- `infra/config/compose/jenkins/image/Dockerfile`: sets readable ownership and
  mode for the Jenkins initialization script; the fresh native reinstall
  exposed the previous image's `600 root:root` mode.

Outside the repository, the Windows host `.wslconfig` memory cap was restored
to its original 20 GB value. No WSL restart occurred. An isolated native VM
candidate copy and protected host-local evidence were created for validation.
