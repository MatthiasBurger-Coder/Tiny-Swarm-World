# Changed Files: #280 / CRED-02

## Product and tests

- `src/tiny_swarm_world/simple_installer.py` — switch the normal installer
  from generated credentials and persistent bootstrap state to the canonical
  internal-test catalog; preserve explicit overrides.
- `tests/test_simple_installer.py` — cover standard mode wiring, deterministic
  fresh/rerun resolution, active manifest keys, special-format credentials,
  explicit overrides, failure handling, and output redaction.
- `tests/test_install_script.py` — execute the actual simple-installer path in
  the install-script fixture and retain separate coverage for legacy modes.
- `src/tiny_swarm_world/domain/configuration/configuration_contract.py` — make
  the internal-test Traefik `htpasswd` exception explicit in the configuration
  contract.
- `documentation/arc42/08_configuration/rc1-simple-secret-bootstrap.md` —
  document the catalog-backed stateless standard contract and boundaries for
  compatibility overrides and follow-up cleanup.
- `documentation/arc42/08_configuration/operator-configuration-contract.md`,
  `documentation/arc42/08_configuration/config-contract-inventory.md`,
  `documentation/arc42/07_deployment_view.adoc`, and
  `documentation/arc42/08_concepts.adoc` — align the Traefik ownership
  boundary with the internal-test catalog exception.
- `documentation/process/skills/audit/skill-registry.json` — refresh the
  governing SHA-256 cache for the changed Arc42 concepts file so the repository
  integrity gate remains valid.

## Evidence and traceability

- `.tiny-swarm/evidence/issue-280/requirement_matrix.md`
- `.tiny-swarm/evidence/issue-280/implementation_summary.md`
- `.tiny-swarm/evidence/issue-280/changed_files.md`
- `.tiny-swarm/evidence/issue-280/test_results.md`
- `.tiny-swarm/evidence/issue-280/remaining_risks.md`
- `.tiny-swarm/evidence/issue-280/acceptance_checklist.md`
- `.tiny-swarm/evidence/issue-280/three-amigos.md`
- `.tiny-swarm/evidence/issue-280/completion_audit.md`

No credential values, tokens, authorization headers, generated local state, or
runtime evidence were added to the tracked change.
