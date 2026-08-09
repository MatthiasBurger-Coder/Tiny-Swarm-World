# Issue #187 — Remaining Risks

- Live service reachability, TLS trust and Docker/Swarm routing remain
  unverified and require explicit consent plus observable evidence.
- The registry preserves current substring matching; future overlapping service
  names require an explicit ordering decision and compatibility tests.
- Browser and external quality-system states remain not run.
