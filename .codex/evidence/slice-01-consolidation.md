# Slice 01 Consolidation

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S01`

Slice title: Repository scan and migration baseline

Stream results:

- Requirement gate: accepted through explicit role-based Three Amigos review.
- Baseline scan: captured RabbitMQ and Pulsar references in tracked repository
  files.
- Deep RabbitMQ coupling scan: no application-level `pika`, `aio_pika`,
  `kombu`, `basic_publish`, `basic_ack`, `exchange`, or `routing_key` coupling
  found outside workflow text.

Accepted findings:

- RabbitMQ currently appears in active platform documentation, configuration,
  desired stack references, tests, and workflow/history material.
- The referenced `documentation/user_guide/troubleshooting.adoc` contains a
  RabbitMQ management endpoint and should be handled in the later
  documentation slice, not Slice 01.
- Slice 01 may proceed because the final Three Amigos decision is accepted.

Rejected findings:

- None.

Files changed per stream:

- documentation/evidence:
  - `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/three-amigos-review.md`
  - `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/rabbitmq-reference-baseline.txt`
  - `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/pulsar-reference-baseline.txt`
  - `.codex/evidence/slice-01-distribution.md`
  - `.codex/evidence/slice-01-consolidation.md`

Conflicts found:

- The Windows-hosted shell does not provide `grep`.
- A broad PowerShell recursive scan encountered ignored local runtime/tool
  artifacts and timed out or reported unreadable symlink-like entries.

Conflicts resolved:

- Used `git grep` over tracked repository files as the stable product baseline
  source for Slice 01.
- Kept local runtime artifacts out of committed evidence.
- Used WSL for the required quality gate because this project is Linux/WSL-only
  and the Windows PATH did not expose the required Python tooling.

Tests executed:

- `git diff --check`
- `git diff --cached --check`
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PATH="$PWD/.venv/bin:$PWD/venv/bin:$PWD/bin:$PATH" python3 tools/quality_gate.py quality'`

Quality-gate result:

- `git diff --check`: passed.
- `git diff --cached --check`: passed.
- `python3 tools/quality_gate.py quality`: passed under WSL using the
  repository-local Linux `.venv`.

Typed Error Router notes:

- Initial Windows PowerShell attempts could not run the required gate with
  `python3` because `python3` was not on PATH.
- `py tools/quality_gate.py quality` started under Python 3.14 but failed at
  `arch-lint` because `lint-imports` was not on Windows PATH.
- Classified as `BUILD_FAILURE` environment routing, then resolved by running
  the required gate in WSL, the repository's supported runtime.

SonarQube findings and fixes:

- Not applicable for Slice 01.

Documentation updates:

- Three Amigos workflow evidence was created.

Final integration decision:

- Accepted. Slice 01 evidence is complete enough to checkpoint, and no Slice 01
  stop condition is active.
