# ARCH-03.01 — Dependency Map

This map records direct imports and technology access at the orchestration
edge. It is intentionally source-level and should be regenerated or reviewed
when ARC-02 through ARC-06 change these modules.

## Direct import map

| Importer | Inner-layer imports | Concrete infrastructure imports | Assessment |
|---|---|---|---|
| `__main__.py` | application services/results/ports and domain policies | `infrastructure.composition`; `infrastructure.adapters.preflight.ensure_common_executable_paths` | Composition import is an allowed edge binding; the direct preflight adapter import is an edge bypass and should move behind composition or an application port. |
| `installer.py` | domain host/filesystem/configuration policies, application filesystem evidence port and credential service | host detector, filesystem inspector, local evidence repository, TLS state adapter | Mixed-boundary legacy installer; concrete adapters are imported alongside orchestration and presentation. |
| `simple_installer.py` | domain credential policy and application credential service | operator configuration loader; legacy installer module | Bootstrap adapter is coupled to concrete file loading and the legacy lifecycle. |
| `infrastructure/composition.py` | none directly; delegates to composition runtime | `composition_runtime` and dynamic capability modules | Intended composition facade with compatibility indirection. |
| `composition_runtime.py` | broad application services and ports; domain contracts | broad concrete client, runner, storage, UI, configuration, logging, and preflight adapters | Expected technology binding location, but broad capability coupling is a migration target. |

## Direct technology access

| Surface | Access observed | Architectural consequence |
|---|---|---|
| `__main__.py` | `asyncio.run`, `os.environ`, `input`, extensive `print`/JSON rendering | Entrypoint owns presentation, consent interaction, and some runtime state interpretation. |
| `installer.py` | `subprocess.run`, `subprocess.Popen`, process-group termination, `Path` reads/writes/mkdir, `os.environ`, `os.killpg`, YAML loading, `input`, console rendering | One module owns process, filesystem, host/runtime, evidence, safety prompts, and lifecycle behavior. Existing process-spawn allowlist explicitly names this file as a legacy boundary. |
| `simple_installer.py` | environment reads, secure `Path`/stat checks, protected file loading, credential resolution, console rendering | Bootstrap concerns and operator presentation are coupled to the legacy installer entrypoint. |
| `composition_runtime.py` | concrete Docker/Incus/LXC/HTTP/command-runner/UI/storage construction | Correct technology boundary in principle; scope is broad and should be split by independently changeable capability. |

## Runtime-specific branching

- `__main__.py` branches on workflow kind, live consent, update mode, provider
  selection, setup profile, and WSL Windows-filesystem allowance.
- `installer.py` branches on native Linux versus WSL, Windows exposure and
  bridge state, configured filesystem locations, reset/live approval, and
  installer subprocess phases.
- `composition_runtime.py` and focused composition modules branch on the LXC
  provider, WSL/native host preparation, and concrete service/client choices.

These branches are product behavior and are not violations by themselves. The
finding is that their policy selection and technology construction are mixed in
the root-level installer/entrypoint surfaces.

## Circular dependency result

An AST graph over package-local imports reports this strongly connected
component:

```text
composition_artifacts
  <-> composition_runtime
  <-> composition_deployment
  <-> composition_platform
  <-> composition_setup
```

The cycle is enabled by compatibility symbol re-exports and runtime refresh
hooks. It is a `HIGH` structural finding because it makes capability extraction
and independent testing harder, while the public facade preserves existing
patch/import compatibility.
