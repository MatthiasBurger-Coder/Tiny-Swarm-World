# ARCH-03.01 — Architecture Violation Map

Status: baseline audit completed 2026-09-13
Issue: #344
Parent: #313 — EPIC 03

## Purpose and method

This document records a source-level dependency and responsibility audit before
the ARC-02 through ARC-06 refactoring slices. It is a baseline, not a refactor
proposal. Findings are based on Python AST import inspection, direct source
inspection, the existing import-linter contracts, and the architecture tests.

File size is included only as context. A finding exists because of dependency
direction, direct technology access, mixed ownership, lifecycle duplication, or
boundary coupling.

The audit covers:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/installer.py`
- `src/tiny_swarm_world/simple_installer.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- root-level modules that import both application/domain and concrete infrastructure
- the focused `infrastructure/composition_*.py` modules that implement the facade

## Current dependency map

```text
CLI entrypoint (__main__.py)
  -> application results, ports, domain policies
  -> infrastructure.composition facade
  -> infrastructure.adapters.preflight.ensure_common_executable_paths  [edge bypass]

Legacy installer (installer.py)
  -> domain policies and application ports/services
  -> concrete infrastructure host, repository, and TLS adapters          [edge bypass]
  -> subprocess, filesystem, environment, YAML, console, process groups

Simple installer (simple_installer.py)
  -> legacy installer module
  -> domain credential policy and application credential service
  -> concrete operator-configuration adapter
  -> filesystem, environment, credential presentation

Composition facade (infrastructure/composition.py)
  -> composition_runtime
  -> dynamic delegation and compatibility patch synchronization

Composition implementation modules
  -> application ports/services and domain policies
  -> concrete infrastructure adapters
  -> composition_runtime compatibility symbols
  -> focused composition modules
```

The application and domain layer contracts remain directionally protected by
`.importlinter` and `tests/architecture/test_hexagonal_imports.py`. The gap is
at the executable and installer edge: root-level modules are allowed to import
both inner-layer concepts and concrete infrastructure, so the existing rules
do not constrain those modules as architectural boundaries.

## Layer and ownership baseline

| Surface | Current classification | Intended primary owner | Baseline observation |
|---|---|---|---|
| `__main__.py` | `ENTRYPOINT`, `PRESENTATION`, `APPLICATION_ORCHESTRATION`, `CROSS_BOUNDARY_DEBT` | Thin entrypoint plus dedicated CLI adapter/dispatcher | Parses arguments, registers workflows, enforces consent, builds services, dispatches workflows, renders JSON/text, and reads environment directly. |
| `installer.py` | `ENTRYPOINT`, `PRESENTATION`, `APPLICATION_ORCHESTRATION`, `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT`, `LEGACY_COMPATIBILITY` | Installer application service plus host/filesystem/process/evidence adapters | Owns installer sequencing and also concrete subprocess, filesystem, YAML, host probing, evidence, log rendering, and Windows/WSL guidance. |
| `simple_installer.py` | `ENTRYPOINT`, `PRESENTATION`, `INFRASTRUCTURE_ADAPTER`, `LEGACY_COMPATIBILITY`, `CROSS_BOUNDARY_DEBT` | Installer CLI/bootstrap adapter | Reads protected files and environment, resolves credentials, delegates to legacy installer, and prints operator access targets. |
| `infrastructure/composition.py` | `COMPOSITION`, `LEGACY_COMPATIBILITY`, `CROSS_BOUNDARY_DEBT` | Composition facade with capability-specific composition owners | Correctly binds the public compatibility surface to composition modules, but dynamic patch synchronization obscures ownership and creates a cycle with implementation modules. |
| `composition_runtime.py` and focused composition modules | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | Capability-specific composition modules | Composition owns concrete adapter construction as intended, but compatibility re-exports and runtime symbol refresh produce broad coupling. |
| `domain/**` | `DOMAIN_POLICY` | Domain | No forbidden application or infrastructure imports found by the existing checks. |
| `application/**` | `APPLICATION_ORCHESTRATION` | Application services and ports | No concrete infrastructure imports found by the existing checks; this is the protected baseline to preserve. |

## Baseline conclusions

1. The core hexagonal direction is currently green under the existing layer
   checks. The audit therefore does not classify ordinary composition imports
   as violations; composition is the intended adapter-binding owner.
2. `__main__.py`, `installer.py`, and `simple_installer.py` are the root-level
   mixed-import set. They are architectural edge exceptions, but they are not
   uniformly governed as entrypoint boundaries.
3. The most consequential issue is responsibility mixing at the edge, not the
   number of lines in any one file.
4. The composition compatibility mechanism is a structural debt hotspot. The
   dependency graph contains a cycle among
   `composition_artifacts`, `composition_deployment`, `composition_platform`,
   `composition_runtime`, and `composition_setup`.
5. No live infrastructure command was run for this audit.

## Fitness baseline for later slices

Future architecture checks should preserve the current rules and add explicit
governance for the following surfaces:

- `__main__.py` may import the composition facade and application/domain types,
  but must not import concrete infrastructure adapters or perform process,
  filesystem, or runtime-client work.
- Installer orchestration may express installation intent, but concrete process,
  host, filesystem, evidence, and presentation concerns must have explicit
  ports/adapters or remain documented legacy compatibility exceptions with an
  owner and removal slice.
- `simple_installer.py` must remain a thin bootstrap/CLI adapter and must not
  become a second installer lifecycle owner.
- Composition may bind concrete adapters, but capability-specific composition
  ownership must be visible and composition cycles must not grow.
- Every remaining mixed-boundary exception must have a named owner, rationale,
  priority, and migration path.

The detailed findings and migration ownership are in
`violation-inventory.md` and `responsibility-ownership.md`; the repeatable
source evidence is in the issue evidence package for #344.
