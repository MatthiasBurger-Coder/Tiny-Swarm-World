# Issue #218 — Slice 05 consolidation

Artifact source readiness is now explicit and bounded:

- `direct-internet`, `nexus`, `fallback`, and `offline` modes are supported.
- HTTP source probes use a configured timeout and accept registry
  authentication challenges as reachability evidence.
- Offline mode is fail-closed and requires a versioned local manifest with
  non-empty artifacts and matching SHA-256 checksums.
- Missing, malformed, unreadable, or mismatched offline artifacts return a
  structured `FAILED` result before platform mutation.
- The composite quality gate passed after this change: 1576 tests, 28 skipped
  in 124.501 seconds; all required local checks exited 0.

The live WSL2 run used direct internet and completed successfully. A live Nexus
cache was not required for that run and no Nexus/Docker/apt mutation was
performed by the readiness probe itself.
