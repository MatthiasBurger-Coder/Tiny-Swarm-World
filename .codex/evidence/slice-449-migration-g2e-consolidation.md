# S449-MIGRATION-G2E consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

The candidate adds only the early, non-admitting migration-check action,
strictly parses its three manually supplied candidate options and emits fixed
redacted operator-local-unverified blocked JSON after the bounded reader has
closed. It does not detect host version, apply a migration, grant capability
support, adopt or persist state, construct runtime services or qualify a host.

Preflight and six same-contract role decisions are recorded in distribution.
Independent candidate reviews and exact-source designated SSH PC WSL
verification are recorded below. No local tests or host operations were
performed by this implementation stream.

The package-entrypoint registry loop previously supplied no options to the
new command. A separately reviewed contract/workflow amendment permitted adding
the three required valid options for this action in that loop. Existing
assertions remain, and a separate negative test still verifies missing options
block before loading.

## Final verification and corrections

The integration owner reports Security and Architecture GO for final source,
Tester GO for final bytes and Requirement/Python GO. DevOps final candidate
GO is also reported for the exact scope and candidate hashes; the earlier
six-role design reviews and S3/S3D are recorded separately in distribution.

On designated SSH PC WSL Python 3.14, the exact-source contract-targeted suite
passed 126 tests, the broader targeted suite passed 225 tests, direct Ruff
passed, and `python3 tools/quality_gate.py quality` passed exit 0: 3,408 tests
run, 37 skipped, 206.196 seconds. `git diff --check` passed. Python 3.12 and
live host execution were not tested.

Architecture review found that the broader SwaggerMode enum admitted
`unknown` at the CLI boundary; it is now rejected before composition and
repository loading. Mixed separate/equals option tests were added. An earlier
broader targeted run failed one documentation assertion because a sentence
wrapped across lines; normalizing test whitespace fixed the false negative
without weakening the expected content. The final targeted and full runs passed
after these corrections.

## CP_RECORD

- sliceId: S449-MIGRATION-G2E
- workflowVersion: 1.63
- sliceTitle: Non-admitting operator migration check
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/infrastructure/adapters/cli/migration_admission.py,
  src/tiny_swarm_world/infrastructure/adapters/cli/parser.py,
  src/tiny_swarm_world/infrastructure/adapters/cli/registry.py,
  src/tiny_swarm_world/infrastructure/composition_lifecycle.py,
  src/tiny_swarm_world/infrastructure/composition.py,
  tests/test_migration_admission_cli.py, tests/test_package_entrypoint.py,
  documentation/user_guide/selective-setup.md,
  .codex/evidence/slice-449-migration-g2e-distribution.md,
  .codex/evidence/slice-449-migration-g2e-consolidation.md
- qualityCommands: contract-targeted and broader SSH PC WSL unittest suites;
  direct Ruff on changed Python files; python3 tools/quality_gate.py quality;
  git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; contract targeted
  126, broader targeted 225, Ruff, full quality exit 0, 3,408 tests run,
  37 skipped, 206.196 seconds
- rollbackReference: cc660e4aa43b363dba375c6e72eecd3ef6d00531
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution not tested. Candidate
  version is manually supplied; no host version detection, positive admission,
  mutation, adoption or runtime qualification is established.
