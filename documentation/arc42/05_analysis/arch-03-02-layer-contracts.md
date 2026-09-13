# ARCH-03.02 — Architecture Layer Contracts

Status: enforced locally 2026-09-13
Issue: #345
Parent: #313 — EPIC 03

## Contract model

The project uses these logical layers:

| Layer | May depend on | Must not depend on |
|---|---|---|
| Domain | Python standard library and domain modules | application, infrastructure, interface adapters, CLI/bootstrap |
| Application | domain and application ports/services | concrete infrastructure adapters, CLI/bootstrap |
| Ports | domain contracts and port types | concrete adapters and application services |
| Infrastructure | application/domain contracts and ports | —; it is the technology-binding layer |
| Interfaces | application services and application/domain contracts | domain implementation details through reverse imports |
| Bootstrap/composition | all contracts and concrete adapters | application services constructing concrete adapters themselves |

“Interfaces” is a logical boundary in this Python repository; there is no
separate `interfaces` package today. If one is introduced, domain imports of
`tiny_swarm_world.interfaces` remain forbidden by the import-linter contract.

## Enforcement

`.importlinter` enforces domain isolation and application isolation. The
architecture regression suite additionally checks that:

- application code cannot import CLI/bootstrap modules;
- `__main__.py` reaches infrastructure only through
  `infrastructure.composition`;
- the deliberately forbidden-import probe is detected as a violation;
- legacy root exceptions are an exact, reviewed allowlist rather than an
  implicit blanket exemption.

The canonical local gate is:

```text
python3 tools/quality_gate.py quality
```

A forbidden import causes `arch-lint` or `arch-tests` to fail and therefore
fails CI. No live infrastructure is needed for this verification.

## Explicit legacy exceptions

The following exceptions remain because ARC-03 has not yet extracted the
legacy installer lifecycle. They are not permission for new bypasses:

| Surface | Exception | Owner | Rationale | Migration |
|---|---|---|---|---|
| `installer.py` | host, local evidence repository, TLS state, UI reporter, WSL bridge adapters | ARC-03 installer owner | Existing installer compatibility surface still sequences lifecycle and presentation | ARC-03 extraction into application ports/adapters |
| `simple_installer.py` | legacy installer and operator configuration adapter | ARC-03 installer owner | Thin bootstrap compatibility entrypoint delegates to the legacy lifecycle | ARC-03 single installer lifecycle owner |

The allowlist is encoded in `tests/architecture/test_hexagonal_imports.py`.
Adding an import requires an explicit architecture review and an update to
this table and its migration rationale; it must not be added only to make a
build green.

## Traceability

ARCH-03.01 identified the root-edge bypasses and assigned ARC-02/ARC-03
owners. This contract slice preserves those documented exceptions while
closing the unregistered `__main__.py` adapter bypass and adding executable
regression checks. The issue evidence package records requirement, changed
files, tests, risks, and acceptance status.
