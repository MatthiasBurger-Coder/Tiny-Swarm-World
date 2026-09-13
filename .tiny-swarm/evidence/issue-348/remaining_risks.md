# Remaining Risks — #348 / ARCH-03.05

- The compatibility composition surface still accepts raw profile/provider
  inputs so existing callers remain stable; it resolves them immediately at
  the boundary.
- Backend executable discovery remains an infrastructure concern and is
  intentionally passed into the pure resolver as capability facts.
- Live Incus, Docker Swarm, compose, browser, and external service checks were
  not applicable and were not run.
