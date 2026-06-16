# Slice 10 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S10`

Slice title: Full automated test run

Affected areas:

- evidence
- repository quality gate
- command probe output

Chosen execution mode: sequential

Selected streams:

- quality
- evidence

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/full-test-run.txt`
- `.codex/evidence/slice-10-distribution.md`
- `.codex/evidence/slice-10-consolidation.md`

Conflict risks:

- The workflow asks for `python -m pytest`, but the project quality contract is
  unittest-based through `tools/quality_gate.py`.
- `install.sh --help` must remain a help probe only and must not trigger live
  infrastructure changes.

Quality gates to run:

- `python3 -m pytest`
- `./install.sh --help || true`
- quality command discovery
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Store command outputs in workflow evidence.
- Classify unavailable pytest separately from the authoritative quality gate.
- Commit only verification evidence for this slice.

Parallelization decision:

- Rejected. The slice is an ordered verification and evidence capture step.
