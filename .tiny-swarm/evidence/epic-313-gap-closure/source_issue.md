# EPIC 03 — Harden Architecture Boundaries and Decompose Orchestration Hotspots

## Purpose

Tiny Swarm World already has a strong hexagonal core with explicit domain/application/infrastructure separation, ports and adapters, automated architecture tests, import-linter contracts, responsibility boundaries and a canonical quality gate.

A source-level architecture audit identified that the remaining structural risk is concentrated primarily at the orchestration edge rather than in the domain/application core. In particular, `src/tiny_swarm_world/__main__.py`, `src/tiny_swarm_world/installer.py` and parts of `src/tiny_swarm_world/infrastructure/composition.py` carry broad responsibilities and are only partially covered by the existing architecture governance.

This EPIC strengthens these boundaries without introducing speculative abstractions or pattern-for-pattern's-sake refactors. The objective is smaller responsibilities, explicit dependency ownership, preserved behavior and machine-verifiable architecture.

## Problem statement

The current architecture rules strongly protect:

- `tiny_swarm_world.domain`
- `tiny_swarm_world.application`
- application ports
- selected responsibility boundaries such as platform, artifacts and deployment

However, root-level orchestration modules are less constrained. This creates a governance blind spot where CLI, installer, composition, filesystem, environment, subprocess, host, credential and presentation responsibilities can accumulate without violating the existing domain/application import contracts.

Current hotspots include:

- `src/tiny_swarm_world/__main__.py`
  - CLI argument parsing
  - workflow registration and routing
  - consent/confirmation handling
  - host/preflight/network dispatch
  - workflow execution orchestration
  - JSON/console presentation
  - direct use of composition builders

- `src/tiny_swarm_world/installer.py`
  - CLI parsing
  - host/runtime detection
  - filesystem and Git probing
  - credential preparation
  - WSL/Windows bridge handling
  - subprocess execution
  - evidence/log handling
  - reset/setup lifecycle orchestration
  - error handling and presentation

- `src/tiny_swarm_world/infrastructure/composition.py`
  - broad wiring responsibilities across multiple capabilities and bounded responsibility areas

The existing architecture tests already acknowledge selected mixed-boundary files. This EPIC turns those known exceptions into a bounded migration target instead of allowing the exception surface to grow.

## Goals

1. Preserve the current domain/application hexagonal architecture and its dependency direction.
2. Make CLI, installer and composition responsibilities explicit and independently testable.
3. Reduce root-level orchestration modules to thin adapters/composition entry points.
4. Extend automated architecture governance so root-level modules cannot become an unrestricted architectural bypass.
5. Reduce the documented mixed-boundary exception set over time.
6. Preserve all current supported Classic behavior, safety controls, consent semantics, evidence contracts and release qualification.
7. Improve readability and change isolation without introducing unnecessary generic frameworks.

## Architecture direction

Target direction, subject to implementation-level Three-Amigos review:

```text
__main__.py
   -> CLI adapter / dispatcher
      -> application use cases / workflow services
         -> application ports
            -> infrastructure adapters

installer entrypoint
   -> installer orchestration application service
      -> explicit ports for host/filesystem/process/evidence/credentials
         -> infrastructure adapters

composition
   -> capability-specific composition modules
      -> one narrow application composition facade where useful
```

Possible CLI decomposition:

```text
adapters/cli/
├── parser.py
├── workflow_registry.py
├── dispatcher.py
├── consent.py
└── renderer.py
```

This is a direction, not a required folder layout. Implementation must prefer the smallest structure that produces clear responsibility ownership.

## Design principles

- Refactor by responsibility, not by file size alone.
- Prefer existing ports and abstractions before creating new ones.
- Create a new port only when a real boundary needs inversion and at least one concrete consumer exists.
- Do not introduce Strategy/Factory/Command/etc. merely to satisfy a design-pattern checklist.
- Keep composition at the system edge.
- Keep domain pure.
- Keep application independent from concrete infrastructure.
- Keep infrastructure adapters focused on technology concerns.
- Keep presentation separate from workflow semantics.
- Preserve explicit live-consent and destructive-operation safeguards.
- No behavior change without an explicit requirement.

## Required audit baseline

Before implementation, produce a source-level responsibility and dependency inventory for at least:

- `src/tiny_swarm_world/__main__.py`
- `src/tiny_swarm_world/installer.py`
- `src/tiny_swarm_world/simple_installer.py`
- `src/tiny_swarm_world/infrastructure/composition.py`
- root-level package modules that import both application/domain and concrete infrastructure

Classify responsibilities as:

- `ENTRYPOINT`
- `PRESENTATION`
- `APPLICATION_ORCHESTRATION`
- `COMPOSITION`
- `INFRASTRUCTURE_ADAPTER`
- `DOMAIN_POLICY`
- `CROSS_BOUNDARY_DEBT`
- `LEGACY_COMPATIBILITY`

For every `CROSS_BOUNDARY_DEBT` item, identify the intended owner and migration path before moving code.

## Work packages

### ARC-01 — Establish architecture and Clean-Code audit baseline
Create a repeatable inventory of large/mixed-responsibility modules, dependency direction, direct technology access, coupling and documented exceptions. Record the desired ownership of each responsibility.

### ARC-02 — Make `__main__.py` a thin CLI entry point
Extract parsing, routing, presentation and command-specific orchestration where this reduces responsibility mixing. Keep the executable entry point focused on bootstrapping and handing control to the CLI adapter.

### ARC-03 — Decompose the installer God-module responsibilities
Separate installer application orchestration from concrete host/filesystem/process/evidence/presentation behavior. Preserve current live-install safety and installation semantics. Avoid rewriting working infrastructure adapters unnecessarily.

### ARC-04 — Modularize composition by capability/boundary
Split broad composition responsibilities where multiple independent capability areas are wired together. Keep one clear composition root while allowing platform/artifacts/deployment/setup/host/network capabilities to be assembled without one ever-growing module.

### ARC-05 — Extend architecture governance to root-level orchestration
Add architecture tests/import contracts that explicitly govern entrypoints, CLI adapters, installer orchestration and composition. Prevent application logic from migrating back into unrestricted root modules.

### ARC-06 — Reduce and govern mixed-boundary exceptions
Review `KNOWN_MIXED_BOUNDARY_FILES` and equivalent documented debt. Every remaining exception must have an owner, rationale and removal/isolation plan. New exceptions require an explicit architecture decision/test update rather than silently accumulating.

### ARC-07 — Verify behavior preservation and regression safety
Run targeted tests plus the canonical quality gate. Ensure supported CLI workflows, installer paths, consent rules, failure states and evidence semantics remain equivalent unless a separately approved requirement changes them.

### ARC-08 — Final independent architecture review
Perform an independent architecture/Clean-Code review against this EPIC's acceptance matrix. Confirm responsibility ownership, dependency direction, testability and remaining debt before closing the EPIC.

## Acceptance criteria

### Architecture
- [ ] Domain remains free of application/infrastructure imports.
- [ ] Application remains free of concrete infrastructure imports.
- [ ] New orchestration behavior is placed in an explicitly owned layer/boundary.
- [ ] Root-level modules cannot act as unrestricted dependency bypasses.
- [ ] CLI presentation does not own infrastructure behavior.
- [ ] Installer application orchestration does not directly own unrelated technology concerns where a stable boundary exists.
- [ ] Composition remains the place where concrete adapters are bound to ports.
- [ ] Broad composition responsibilities are split where independently changeable capability areas exist.

### `__main__.py`
- [ ] `__main__.py` is demonstrably thinner and has one primary responsibility: executable bootstrap/CLI delegation.
- [ ] Workflow parsing/routing/presentation responsibilities have explicit owners.
- [ ] Existing workflow names, safety semantics and exit behavior remain covered by regression tests.

### Installer
- [ ] Installer responsibilities are inventoried before refactoring.
- [ ] Installer orchestration is separable from concrete subprocess/filesystem/host/evidence/presentation concerns.
- [ ] WSL2/native-Linux behavior remains supported according to existing product contracts.
- [ ] Reset/setup ordering, failure propagation and evidence generation remain deterministic.
- [ ] Credential and redaction behavior is not weakened.

### Governance
- [ ] Architecture tests cover the newly established CLI/installer/composition boundaries.
- [ ] The architecture gate fails when prohibited cross-boundary imports or direct technology access are deliberately introduced in protected areas.
- [ ] Known mixed-boundary exceptions are reduced or explicitly justified with owner and follow-up.
- [ ] No new architecture exception is introduced merely to make tests pass.
- [ ] Architecture documentation and ADR/debt documentation reflect the implemented structure.

### Clean Code / maintainability
- [ ] Materially changed modules have clear single primary responsibilities.
- [ ] Naming reflects domain/application/infrastructure intent rather than generic helpers/managers.
- [ ] No new generic abstraction is introduced without a concrete use case.
- [ ] Duplicated orchestration is removed when a canonical owner exists.
- [ ] Dependency injection is used at real technology boundaries rather than for trivial pure functions.
- [ ] Error handling remains explicit and does not hide failure states.

### Verification
- [ ] Targeted architecture tests pass.
- [ ] Targeted CLI and installer regression tests pass.
- [ ] `python3 tools/quality_gate.py quality` passes on the final integrated candidate, or an external/non-code blocker is recorded truthfully according to repository policy.
- [ ] No required RC1/live acceptance result is invalidated by this refactor without rerunning the affected scenario.

## Three-Amigos scenarios

### CLI change
**Given** a developer adds a new CLI command
**When** the command is implemented
**Then** parsing/presentation stays in the CLI adapter
**And** application behavior is implemented behind the appropriate application service/port boundary
**And** concrete infrastructure is wired through composition.

### Installer capability change
**Given** a new host/install capability requires filesystem or subprocess access
**When** it is implemented
**Then** installer orchestration expresses the workflow intent
**And** concrete technology behavior belongs to an adapter
**And** the workflow can be tested without executing live infrastructure.

### Architecture regression
**Given** application code directly imports a concrete infrastructure adapter
**When** the architecture quality gate runs
**Then** the build fails with an actionable architecture violation.

### Root-level bypass regression
**Given** new application logic is placed into an unrestricted package-root module to avoid layer rules
**When** architecture tests run
**Then** the violation is detected or the module must first be explicitly classified and governed.

### Pattern restraint
**Given** existing code can be cleanly decomposed with functions/classes and existing ports
**When** refactoring occurs
**Then** no unnecessary generic framework or design pattern hierarchy is introduced solely for stylistic consistency.

## Non-goals

This EPIC must not:

- redesign the domain model without a separate requirement;
- replace the current Classic Docker Swarm behavior;
- implement the future Podman/Kubernetes vision;
- change credential semantics owned by EPIC 02 unless required to preserve existing contracts;
- weaken live-consent, destructive-operation or evidence safeguards;
- broadly rename packages only for aesthetics;
- enforce arbitrary maximum file sizes as an architecture rule;
- introduce patterns solely because a pattern catalog recommends them;
- perform unrelated performance optimization;
- claim live verification without actual live evidence.

## Execution order

1. ARC-01 — establish responsibility/dependency baseline.
2. ARC-05 — define/extend guardrails early so refactoring cannot drift.
3. ARC-02 — thin CLI entry point.
4. ARC-03 — decompose installer responsibilities incrementally.
5. ARC-04 — modularize composition as required by extracted responsibilities.
6. ARC-06 — reduce documented exception surface.
7. ARC-07 — full regression/quality verification.
8. ARC-08 — independent completion audit.

ARC-02/03/04 may proceed in slices after the baseline, but each slice must preserve green architecture and behavioral tests.

## Definition of Done

EPIC 03 is complete when Tiny Swarm World's already strong hexagonal core is matched by equally explicit orchestration-edge boundaries: CLI, installer and composition have clear responsibility ownership; root-level modules are no longer an architectural blind spot; mixed-boundary exceptions are reduced and governed; supported behavior and safety contracts remain intact; and the architecture is enforced by automated tests rather than documentation alone.

The desired outcome is not "more architecture". It is a smaller, clearer and harder-to-accidentally-degrade architecture that remains understandable to human developers and AI-assisted contributors alike.

## Resulting architecture documentation — ARCH-03.21

Tracked by [#364](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/364).
The resulting ownership, dependency, Classic runtime, composition, planning,
configuration/secret/process boundaries, fitness functions and runtime extension
path are documented in
[ARCH-03.21 — Resulting architecture and runtime extension path](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/blob/main/documentation/arc42/05_analysis/arch-03-21-resulting-architecture.md),
linked from the [Developer Manual](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/blob/main/documentation/manuals/developer-manual.md#architecture).

Publication state: [PR #436](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/436)
was merged to main on 2026-10-03 (merge commit `9fc5fd439805e0864e4bc6741de6dd08f7746d0a`).
Issue #364 is closed and the guide is available through the links above. CI for
Python 3.12/3.13/3.14, the canonical quality gate and the PR SonarCloud quality
gate all passed. This reference does not mark the remaining EPIC work or live
verification complete.
