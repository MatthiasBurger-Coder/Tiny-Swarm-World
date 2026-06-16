# Slice 09 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S09`

Slice title: Global RabbitMQ residue check

Affected areas:

- evidence
- final reference classification
- residual active references if found

Chosen execution mode: sequential

Selected streams:

- validation
- documentation classification

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/rabbitmq-reference-final.txt`
- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/pulsar-reference-final.txt`
- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/final-reference-classification.md`
- `.codex/evidence/slice-09-distribution.md`
- `.codex/evidence/slice-09-consolidation.md`

Conflict risks:

- Workflow and evidence files intentionally mention RabbitMQ and must be classified as historical/migration evidence.
- Active code or configuration residue must be fixed before the slice can complete.

Quality gates to run:

- Required final reference scans.
- `python3 tools/quality_gate.py quality` if any active files are changed outside evidence.

Consolidation plan:

- Generate final RabbitMQ and Pulsar reference files.
- Classify remaining RabbitMQ references.
- Fix any active runtime/config/contract references.

Parallelization decision:

- Rejected. Classification depends on the final whole-repository scan.
