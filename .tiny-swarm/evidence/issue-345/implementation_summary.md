# Implementation Summary — #345 / ARCH-03.02

Implemented and enforced the formal Python layer contracts.

- Added Import-Linter contracts for domain isolation and application isolation
  from CLI/bootstrap entrypoints.
- Routed the `__main__.py` executable-path check through the Composition facade;
  it no longer imports a concrete preflight adapter.
- Added architecture regression checks for application CLI imports, root
  entrypoint adapter access, explicit legacy exceptions, and a synthetic
  forbidden import.
- Documented the logical interfaces layer, allowed dependency direction,
  enforcement commands, and the two existing installer exceptions with owner,
  rationale, and migration slice.

No live infrastructure or external service was used.
