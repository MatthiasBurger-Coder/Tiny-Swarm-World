# Issue #191 — Changed Files

Production:

- src/tiny_swarm_world/infrastructure/adapters/clients/lxc/node/evidence.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc/profile/policy.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc/resource/resolution.py
- src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py
- src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py

Tests:

- tests/infrastructure/adapters/clients/lxc/node/test_evidence.py

Governance/evidence:

- .tiny-swarm/evidence/solid-typed-evidence/requirement_matrix.md
- .tiny-swarm-world/evidence/solid-typed-evidence/three-amigos.md
- .tiny-swarm-world/evidence/solid-typed-evidence/evidence-key-inventory-before.md
- .tiny-swarm-world/evidence/solid-typed-evidence/evidence-key-inventory-after.md
- .codex/evidence/issue-191-20260809/slice-01-*
- .codex/evidence/issue-191-20260809/slice-02-*
- .codex/evidence/issue-191-20260809/slice-03-*

All production changes remain inside the declared S191-02 locks. No live
infrastructure or generated artifact was changed.
