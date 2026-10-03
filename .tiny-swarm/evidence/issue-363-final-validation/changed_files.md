# Changed files

Scoped integration commits:

- `bdd73f58`: `documentation/process/skills/audit/skill-registry.json`, `tests/test_windows_wsl_bridge_assets.py`, and quality-findings evidence.
- `8819d5d3`: `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py`, `tests/infrastructure/adapters/clients/test_lxc_node_provider.py`, and node-mutation evidence.
- `89357c4a`: `tests/e2e/classic/run_credential_transition_live.py`, `tests/e2e/classic/test_credential_transition_runner.py`, and credential-cookie evidence.

Final campaign documentation and the sanitized issue evidence package are root-owned. Exact committed file lists remain available from `git show --stat` for each scoped commit. No service resource policy, command, image context, security configuration or credential value is changed by these three commits.

Final documentation-only gate: `git diff --check` plus JSON/checksum/traceability validation. The full Python gate is not rerun for evidence-only edits because source and tests remain exactly the already reviewed final candidate; the retained runtime gate was executed against matching code. This is the documented QUALITY.md exception for documentation-only changes.
