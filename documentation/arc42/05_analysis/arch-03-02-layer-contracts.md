# ARCH-03.02 — Architecture Layer Contracts

Status: first enforced locally 2026-09-13; EPIC gap-closure boundaries updated 2026-10-03
Issue: #345
Parent: #313 — EPIC 03

## Contract model

The project uses these logical layers:

| Layer | May depend on | Must not depend on |
|---|---|---|
| Domain | Python standard library and domain modules | application, infrastructure, interface adapters, CLI/bootstrap |
| Application | domain and application ports/services | concrete infrastructure adapters, CLI/bootstrap |
| Ports | domain contracts and port types | concrete adapters and application services |
| Infrastructure | application/domain contracts and ports | executable/bootstrap compatibility facades |
| Interfaces | application services and application/domain contracts | domain implementation details through reverse imports |
| Bootstrap/composition | all contracts and concrete adapters | application services constructing concrete adapters themselves |

“Interfaces” is a logical boundary in this Python repository; there is no
separate `interfaces` package today. If one is introduced, domain imports of
`tiny_swarm_world.interfaces` remain forbidden by the import-linter contract.

## Enforcement

`.importlinter` enforces domain isolation and application isolation. The
architecture regression suite additionally checks that:

- application code cannot import CLI/bootstrap modules;
- `__main__.py` reaches infrastructure only through the canonical CLI dispatcher;
- installer roots reach only dependency-light installation composition;
- executable bodies remain delegation-only; installer application code cannot
  acquire direct process/filesystem/state access;
- CLI rendering cannot construct or execute workflows;
- the deliberately forbidden-import probe is detected as a violation;
- outward compatibility exports are exact, reviewed boundaries rather than
  implicit blanket exemptions; infrastructure cannot import those root facades.

The canonical local gate is:

```text
python3 tools/quality_gate.py quality
```

A forbidden import causes `arch-lint` or `arch-tests` to fail and therefore
fails CI. No live infrastructure is needed for this verification.

## Exact executable and compatibility boundaries

The initial #345 contract retained installer adapter exceptions pending ARC-03.
Those historical exceptions were removed when EPIC #313 extracted the lifecycle.
Current root boundaries are:

| Surface | Allowed infrastructure boundary | Owner / rationale |
|---|---|---|
| `__main__.py` | `infrastructure.adapters.cli.dispatcher` | CLI owner; executable delegation |
| `installer.py`, `simple_installer.py` | `infrastructure.composition_installation` | Python automation owner; dependency-light composition and outward imports |
| `prepare_linux.py` | `composition_native_preparation`, `composition_installation` | Host preparation owner; independent native preparation and dependency-light Python bootstrap |
| `cli_presentation.py` | `infrastructure.adapters.cli.presentation` | CLI owner; outward compatibility exports only |

Installation application services consume six ports and have no concrete
adapter imports. Configuration/credentials, host, process, evidence and
presentation implementations are separately owned installation adapters.
Existing installation helper/value exports remain compatibility debt; they do
not authorize root sequencing or reverse imports.

The exact boundaries are encoded in both architecture test modules. Adding an
import requires explicit architecture review, rather than expanding an allowlist
solely to make a gate green. Mutation probes reject root orchestration growth,
application technology/state access, renderer workflow construction and
adapter-to-bootstrap imports. `.importlinter` also enforces the latter boundary.

ARCH-03.19 runs both modules through the canonical `arch-tests` gate in CI.
The regression suite resolves relative imports and reports file, line, rule and
imported module. For `from package import name`, the scan checks whether `name`
is a source submodule before applying the exact package boundary. Wildcards
cannot use a legacy exception. Existing cyclic composition edges from
ARCH-03.01, including later network capability and facade edges, remain bounded:
removed edges are welcome, while new cycle edges fail. The scan does not execute
product code.

## Traceability

ARCH-03.01 identified the root-edge bypasses and assigned ARC-02/ARC-03
owners. The original contract slice governed those exceptions; the gap-closure
implementation moves their responsibilities to explicit owners and replaces
installer exceptions with exact composition boundaries and executable
regression checks. The issue evidence package records requirement, changed
files, tests, risks, and acceptance status.
