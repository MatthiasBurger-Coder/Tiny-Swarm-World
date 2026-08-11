# I197-S04 Consolidation

Workflow: `issue-197-20260809`
Slice: `I197-S04`
Dependency: `I197-S03` / `89828ad`

## Consolidated result

- Composition now constructs `WslSocatExposureAdapter` and injects it into the
  WSL exposure step.
- `SocatManager` remains responsible only for profile-derived forwarding
  command planning.
- Availability, process inspection and process startup are delegated through
  `PortWslSocatExposure`.
- The old composition-local `pgrep`, `sh`, `nohup` helper functions are gone.
- Expose workflow ordering remains LXC exposure first, WSL Socat exposure
  second; the workflow still has exactly two steps.
- `VerificationResult` status, messages and evidence classifications remain
  unchanged.
- `composition_lxc_runtimes.py` and the Socat manager were reviewed and need no
  unrelated changes.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition`: **PASS** — 95 tests.
- `python3 tools/quality_gate.py lint`: **PASS**.
- `git diff --check`: **PASS**.
- Static scan: composition has no `pgrep`, `nohup` or `create_subprocess_exec`
  Socat helper; remaining `subprocess` usage is the pre-existing LXC host-IP
  probe and is outside Socat ownership.
- No live Socat, LXC, Incus, Docker or Swarm command was run.

Decision: **PASS — S197-S04 complete; release to S197-S05.**
