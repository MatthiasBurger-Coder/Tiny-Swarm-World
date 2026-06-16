# Slice 08 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S08`

Slice title: Update documentation and arc42

Affected areas:

- documentation
- architecture docs
- operational readiness
- agent instructions

Chosen execution mode: sequential

Selected streams:

- documentation
- architecture
- operational readiness

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `README.md`
- `documentation/**`
- `OPERATIONAL_READINESS_CHECKLIST.md`
- `infra/AGENTS.md`
- `AGENTS.md`
- `.codex/evidence/slice-08-distribution.md`
- `.codex/evidence/slice-08-consolidation.md`

Conflict risks:

- Historical workflow/ADR references may still mention RabbitMQ and must not be rewritten as current behavior.
- Pulsar standalone must be documented as local-development greenpath, not production cluster parity.
- User-facing docs must not imply Pulsar Manager exists.

Quality gates to run:

- `python3 -m pytest tests -k "documentation or docs or arc42"` if available.
- `python3 tools/quality_gate.py quality`
- RabbitMQ residue scan for active docs.

Consolidation plan:

- Replace active RabbitMQ documentation with Pulsar.
- Update routes and port tables to `/pulsar`, `6650`, and `8087`.
- Add transparent risks for Pulsar resource footprint, standalone mode, and admin port collision.

Parallelization decision:

- Rejected. The docs are semantically coupled and must present one consistent architecture narrative.
