# Slice 11 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S11`

Slice title: Live greenpath validation

Affected areas:

- live validation evidence
- safety boundary documentation

Chosen execution mode: sequential

Selected streams:

- platform verification
- evidence

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/live-greenpath-not-run.md`
- `.codex/evidence/slice-11-distribution.md`
- `.codex/evidence/slice-11-consolidation.md`

Conflict risks:

- Running `./install.sh` would trigger live platform setup and may create or
  mutate LXD/LXC, Docker Swarm, networking, and deployed services.
- Root `AGENTS.md` forbids live infrastructure commands unless explicitly
  approved.

Quality gates to run:

- No live commands.
- Documentation/evidence-only validation with `git diff --check`.

Consolidation plan:

- Record why live greenpath was not run.
- List the exact commands required for manual validation.
- Commit the not-run evidence separately.

Parallelization decision:

- Rejected. The slice is a safety-gated live validation decision.
