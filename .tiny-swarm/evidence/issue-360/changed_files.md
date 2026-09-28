# Changed files

- `src/tiny_swarm_world/installer.py`: removed one dead no-op call/helper and delegated secret-name defaults to the domain policy.
- `src/tiny_swarm_world/simple_installer.py`: removed duplicate secret-name default helper and uses the shared policy.
- `src/tiny_swarm_world/domain/configuration/configuration_contract.py`: owns canonical Traefik secret-name defaults and selection semantics.
- `tests/test_installer.py`: replaced no-op test with retained phase behavior test and added direct installer empty-value regression.
- `tests/test_simple_installer.py`: tests absent/custom/empty secret-name bootstrap handoff.
- `documentation/arc42/05_analysis/arch-03-17-dead-path-audit.md`: records ownership, reference evidence, and retained compatibility code.
- `.tiny-swarm/evidence/issue-360/`: issue requirement and verification evidence (ignored local evidence directory).
