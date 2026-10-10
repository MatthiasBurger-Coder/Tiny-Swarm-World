# ARCH-03.01 — Architecture Violation Inventory

Status: historical ARCH-03.01 finding inventory, with current dispositions
reviewed against the implemented ownership on 2026-10-10. Original locations,
severities and proposed migrations below belong to the pre-refactoring snapshot.

## Current disposition of baseline findings

| Baseline IDs | Implemented owner / current disposition |
|---|---|
| V-001, V-007 | `__main__.py` delegates to the CLI dispatcher. Parser, registry, consent and rendering live under infrastructure CLI adapters. |
| V-002, V-004 | InstallationService, InstallationPhases and InstallationRunEvidence own orchestration through six installation ports; focused adapters own technology. Root exports remain compatibility surfaces. |
| V-003 | Installer process details are behind the installation process adapter and centralized infrastructure process runners; root bootstrap no longer creates child processes directly. |
| V-005, V-011, V-012 | Existing composition refresh/facade cycles remain bounded compatibility debt. Extraction must preserve current patch seams and architecture guards. |
| V-006 | Two credential-resolution stages remain intentionally distinct consumers of the shared resolver; duplicated default selection was consolidated. They are not two lifecycle owners. |
| V-008 | CLI and installer have separate infrastructure presentation owners for different result contracts; a shared renderer is not required. |
| V-009 | Installation ports and typed options/results govern the extracted boundary; CLI Namespace and established composition mappings retain their explicitly documented scopes. |
| V-010 | Protected operator-file loading is owned by installation bootstrap/configuration adapters rather than the executable package-root body. |
| V-013 | Architecture regression tests enforce root delegation, installation boundaries and mutation/import guards. Retained outward exports and composition debt are described in ARCH-03.21. |

See [resulting architecture](arch-03-21-resulting-architecture.md),
[responsibility ownership](arch-03-01-responsibility-ownership.md) and
[layer contracts](arch-03-02-layer-contracts.md) for current owners and safeguards.
These dispositions describe repository structure; they are not new live or
external verification results and do not erase historical severity evidence.

## Original baseline inventory

Severity meanings: `CRITICAL` blocks the intended layer direction or can make
technology behavior bypass the governed application boundary; `HIGH` is a
material edge-boundary or cycle risk; `MEDIUM` is a contained cross-boundary
coupling; `DEBT` is maintainability work that does not currently break the core
layer direction.

## Critical and high findings

| ID | Severity | Finding and evidence | Classification | Intended owner | Migration path |
|---|---|---|---|---|---|
| V-001 | HIGH | `__main__.py:63` imports `infrastructure.adapters.preflight.ensure_common_executable_paths` directly while also importing application/domain types and the composition facade. | `CROSS_BOUNDARY_DEBT` | CLI adapter/composition | ARC-02: move executable-path preparation behind an application port or composition-owned builder; add a root-entrypoint import guard. |
| V-002 | HIGH | `installer.py:29-36` imports concrete host, filesystem evidence, and TLS infrastructure adapters while owning installer orchestration. | `CROSS_BOUNDARY_DEBT`, `LEGACY_COMPATIBILITY` | Installer application service plus infrastructure adapters | ARC-03: extract stable installer ports and move concrete construction to composition; preserve the legacy module as a delegating compatibility surface during migration. |
| V-003 | HIGH | `installer.py` directly runs subprocesses at lines 932, 1172, 1610, and 1631, including process-group termination and Docker/Incus command phases. | `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | Process runner adapter | ARC-03: route phase execution and probes through explicit process/command ports; retain safety and timeout semantics in tests. |
| V-004 | HIGH | `installer.py` combines reset/setup sequencing with filesystem writes, YAML parsing, evidence/log creation, environment mutation, prompts, and console failure guidance. | `APPLICATION_ORCHESTRATION`, `INFRASTRUCTURE_ADAPTER`, `PRESENTATION`, `CROSS_BOUNDARY_DEBT` | Installer application service, evidence adapter, presentation adapter | ARC-03: split by responsibility seams already represented by `InstallerPaths`, `InstallReporter`, evidence helpers, and process helpers; do not split by line count alone. |
| V-005 | HIGH | The package-local import graph contains a cycle among `composition_artifacts`, `composition_deployment`, `composition_platform`, `composition_runtime`, and `composition_setup`. | `COMPOSITION`, `CROSS_BOUNDARY_DEBT` | Capability-specific composition modules | ARC-04: replace compatibility symbol refresh with explicit capability dependencies and a single direction toward shared composition primitives; add cycle detection to architecture checks. |
| V-006 | HIGH | `simple_installer.py` prepares credentials and environment, then delegates to `legacy.run`; `installer.run` performs overlapping installer secret resolution and lifecycle setup. | `LEGACY_COMPATIBILITY`, `CROSS_BOUNDARY_DEBT` | Installer CLI/bootstrap adapter | ARC-03: define one credential/bootstrap owner and make the simple entrypoint pass a typed request into it. |

## Medium findings and maintainability debt

| ID | Severity | Finding and evidence | Classification | Intended owner | Migration path |
|---|---|---|---|---|---|
| V-007 | MEDIUM | `__main__.py` contains workflow registry, argument parsing, consent policy, service construction, dispatch, result normalization, JSON rendering, and text rendering. | `ENTRYPOINT`, `PRESENTATION`, `APPLICATION_ORCHESTRATION`, `CROSS_BOUNDARY_DEBT` | CLI parser/dispatcher/renderer | ARC-02: extract the smallest independently owned CLI seams while keeping the entrypoint as bootstrap/delegation. |
| V-008 | MEDIUM | `__main__.py` and `installer.py` both own operator-facing summaries, failure guidance, and lifecycle status rendering. | `PRESENTATION`, `CROSS_BOUNDARY_DEBT` | CLI/installer presentation adapters | ARC-02/03: establish explicit renderer ownership and keep workflow result semantics in application services. |
| V-009 | MEDIUM | Raw `argparse.Namespace`, mutable environment mappings, `Path` values, and broad service aggregates cross entrypoint/composition boundaries. | `CROSS_BOUNDARY_DEBT` | Application request/result types and composition | ARC-02/03/04: introduce typed boundary requests only where a concrete consumer exists; preserve existing ports first. |
| V-010 | MEDIUM | `simple_installer.py` directly loads operator configuration through `composition_operator_configuration` and performs POSIX ownership/mode checks. | `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | Credential/configuration adapter | ARC-03: keep secure path policy explicit, but move file loading behind a port owned by the installer boundary. |
| V-011 | DEBT | `composition.py` uses dynamic `__getattr__`, importlib delegation, runtime symbol refresh, and facade patch synchronization to preserve old patch points. | `COMPOSITION`, `LEGACY_COMPATIBILITY` | Composition facade owner | ARC-04/06: retain compatibility until consumers are migrated, then reduce dynamic surface and document remaining exceptions. |
| V-012 | DEBT | `composition_runtime.py` remains a broad compatibility/export hub even after focused modules exist. | `COMPOSITION`, `CROSS_BOUNDARY_DEBT` | Capability composition owners | ARC-04: move shared primitives to narrow modules and keep capability builders in their own composition boundary. |
| V-013 | DEBT | Root-level mixed modules are not represented by a dedicated allowlist/contract with owner metadata; existing tests mostly protect inner layers and process-spawn allowlisting. | `CROSS_BOUNDARY_DEBT` | Architecture governance | ARC-05/06: add explicit root-boundary tests and a reviewed exception registry. |

No `CRITICAL` finding was assigned in this baseline. The core domain and
application direction is protected and currently passes the existing checks;
the findings are high-risk orchestration-edge exceptions and composition debt.
