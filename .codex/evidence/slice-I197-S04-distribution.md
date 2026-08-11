# I197-S04 Distribution

Workflow: `issue-197-20260809`
Slice: `I197-S04`
Dependency: `I197-S03` / `89828ad`

## Execution decision

- Execution mode: serial, per the user-requested issue order.
- Primary role: Senior Python Automation Developer.
- Fallback reviewers: Senior System Architect and Senior Tester; real
  subagent tools were not available in this session.
- Parallelization decision: not split. Composition wiring, workflow order and
  result semantics share the `I197-composed-expose-contract` lock.

## Locked scope

- Construct `WslSocatExposureAdapter` in the composition root.
- Inject it into `_WslSocatExposeStep` alongside `SocatManager`.
- Route availability, process-exists and start operations through the adapter.
- Remove the old `pgrep`/`sh`/`nohup` helpers from composition.
- Preserve the two-step expose workflow order and result/evidence fields.
- Update composition tests to patch the adapter-owned optional-tool lookup.

## Safety constraints

- Consent remains checked before adapter availability or process operations.
- No live Socat, LXC, Incus, Docker or Swarm command is run.
- `composition_lxc_runtimes.py` and `SocatManager` are reviewed for impact;
  no unrelated changes are made where no Socat process ownership exists.
