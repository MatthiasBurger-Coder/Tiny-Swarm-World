# ARCH-03.03 — Orchestration Hotspot Inventory and Ranking

Status: source-level ranking completed 2026-09-13

Issue: #346

Parent: #313 — EPIC 03

Predecessor: #344 / ARCH-03.01; #345 / ARCH-03.02

## Purpose and scope

This is the current orchestration-edge inventory before ARC-02 through ARC-06
implementation work. It covers the executable and installer entrypoints plus
every `infrastructure/composition*.py` module that participates in adapter
binding or compatibility delegation:

- `__main__.py`
- `installer.py`
- `simple_installer.py`
- all 12 `infrastructure/composition*.py` modules

The protected domain and application packages are recorded as control surfaces,
not hotspots: ARCH-03.02 and the architecture gate show that they do not have
the concrete-infrastructure dependency pattern being ranked here.

## Reproducible method

The measurements are source-level and do not execute product workflows or live
infrastructure. Re-run from the repository root with:

```bash
python3 - <<'PY'
import ast, pathlib, subprocess

root = pathlib.Path("src/tiny_swarm_world")
paths = [root / "__main__.py", root / "installer.py", root / "simple_installer.py"]
paths += sorted((root / "infrastructure").glob("composition*.py"))
for path in paths:
    source = path.read_text()
    tree = ast.parse(source)
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    imports |= {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    branches = sum(isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
                                   ast.With, ast.AsyncWith, ast.IfExp, ast.Match))
                   for n in ast.walk(tree))
    boolean_edges = sum(max(0, len(n.values) - 1) for n in ast.walk(tree)
                        if isinstance(n, ast.BoolOp))
    side_effect_tokens = sum(source.count(token) for token in (
        "subprocess.", "Path(", "open(", "os.environ", "print(", "input(",
        "yaml.", "asyncio.run("))
    changes = subprocess.run(
        ["git", "rev-list", "--count", "HEAD", "--since=2026-06-01", "--", str(path)],
        check=True, capture_output=True, text=True).stdout.strip()
    print(path, len(source.splitlines()), len(classes), len(functions),
          max((n.end_lineno - n.lineno + 1 for n in functions), default=0),
          1 + branches + boolean_edges, side_effect_tokens, len(imports), changes)
PY
```

The reported complexity is an AST branching indicator, not a claim of exact
McCabe complexity. `side_effect_tokens` is a repeatable proxy for direct
technology and presentation effects. Responsibility count and test-friction
score are reviewed signals: they are assigned from the responsibility map,
direct dependency map, and existing test seams, not inferred from line count.

## Ranking criteria

Each dimension is converted to a 0–5 band. The score is deliberately weighted
toward behavior and coupling:

| Signal | Band thresholds | Weight |
|---|---|---:|
| AST complexity indicator | 0–10, 11–30, 31–60, 61–100, 101–150, >150 | 4 |
| Direct side-effect proxy | 0, 1–5, 6–15, 16–30, 31–50, >50 tokens | 3 |
| Import fan-out | 0–5, 6–10, 11–20, 21–35, 36–60, >60 imports | 3 |
| Responsibility count | 0–1, 2, 3, 4, 5, 6+ responsibilities | 2 per responsibility count |
| Change frequency since 2026-06-01 | 0–1, 2–4, 5–9, 10–19, 20–29, 30+ commits | 2 |
| Test-friction proxy | 0–5 reviewed from concrete dependencies, effects, and seams | 2 |

The resulting score is a comparison aid, not an automatic refactoring order.
Severity is raised when a module is an architectural bypass, owns a lifecycle,
or participates in the compatibility cycle. File size alone cannot produce a
HIGH or CRITICAL result.

## Complete inventory and ranking

| Rank | Surface | Score | Class | Size context (LOC / max function) | Key measured signals | Responsibilities / test friction | Severity and decision |
|---:|---|---:|---|---|---:|---|
| 1 | `installer.py` | 82 | `ENTRYPOINT`, `APPLICATION_ORCHESTRATION`, `INFRASTRUCTURE_ADAPTER`, `PRESENTATION`, `LEGACY_COMPATIBILITY`, `CROSS_BOUNDARY_DEBT` | 1,655 / 218 | complexity 191; effects 71; fan-out 28; 31 changes | 9 / 5 | **CRITICAL** — one lifecycle owner must be separated from process, host/filesystem, evidence, credentials, and presentation adapters. |
| 2 | `__main__.py` | 72 | `ENTRYPOINT`, `APPLICATION_ORCHESTRATION`, `PRESENTATION`, `CROSS_BOUNDARY_DEBT` | 1,097 / 118 | complexity 166; effects 61; fan-out 22; 23 changes | 6 / 4 | **HIGH** — extract parser, registry/dispatcher, consent, and renderer behind a thin executable bootstrap. |
| 3 | `infrastructure/composition_runtime.py` | 63 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | 1,720 / 114 | complexity 72; effects 15; fan-out 76; 8 changes | 8 / 5 | **HIGH** — split capability binding into explicit composition owners and shared primitives; preserve the facade contract. |
| 4 | `simple_installer.py` | 41 | `ENTRYPOINT`, `PRESENTATION`, `INFRASTRUCTURE_ADAPTER`, `LEGACY_COMPATIBILITY`, `CROSS_BOUNDARY_DEBT` | 238 / 34 | complexity 34; effects 20; fan-out 11; 5 changes | 4 / 3 | **MEDIUM** — make it a thin typed bootstrap and remove overlapping credential/lifecycle ownership. |
| 5 | `infrastructure/composition_deployment.py` | 37 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | 461 / 292 | complexity 41; effects 3; fan-out 14; 9 changes | 4 / 4 | **HIGH** — extract deployment capability construction from the 292-line method and make dependencies explicit. |
| 6 | `infrastructure/composition_configuration.py` | 33 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER` | 290 / 16 | complexity 35; effects 9; fan-out 9; 7 changes | 4 / 2 | **MEDIUM** — isolate configuration resolution from composition assembly and retain precedence contracts. |
| 7 | `infrastructure/composition.py` | 32 | `COMPOSITION`, `LEGACY_COMPATIBILITY`, `CROSS_BOUNDARY_DEBT` | 252 / 12 | complexity 12; effects 0; fan-out 5; 68 changes | 4 / 5 | **HIGH** — remove dynamic compatibility refresh cycles through explicit facade-to-capability direction. |
| 8 | `infrastructure/composition_lxc_runtimes.py` | 30 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER` | 401 / 28 | complexity 40; effects 0; fan-out 11; 3 changes | 4 / 3 | **MEDIUM** — keep provider-specific runtime construction cohesive while reducing cross-capability imports. |
| 9 | `infrastructure/composition_setup.py` | 28 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | 365 / 159 | complexity 11; effects 4; fan-out 10; 4 changes | 4 / 4 | **MEDIUM** — isolate setup capability assembly and keep phase ordering in the application workflow. |
| 10 | `infrastructure/composition_platform.py` | 21 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER`, `CROSS_BOUNDARY_DEBT` | 395 / 258 | complexity 10; effects 3; fan-out 2; 1 change | 5 / 4 | **MEDIUM** — split provider/platform wiring at capability seams; do not split solely because one function is large. |
| 11 | `infrastructure/composition_probes.py` | 20 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER` | 248 / 43 | complexity 29; effects 5; fan-out 9; 1 change | 3 / 2 | **MEDIUM** — keep probes technology-focused and expose them through narrow composition inputs. |
| 12 | `infrastructure/composition_artifacts.py` | 12 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER` | 189 / 93 | complexity 5; effects 0; fan-out 2; 1 change | 3 / 3 | **LOW** — monitor; extract only if artifact binding becomes independently changeable. |
| 13 | `infrastructure/composition_models.py` | 11 | `COMPOSITION` | 112 / 2 | complexity 1; effects 0; fan-out 8; 2 changes | 2 / 1 | **LOW** — shared typed models are not an orchestration hotspot by current evidence. |
| 14 | `infrastructure/composition_operator_configuration.py` | 6 | `COMPOSITION`, `INFRASTRUCTURE_ADAPTER` | 14 / 3 | complexity 1; effects 0; fan-out 3; 1 change | 2 / 1 | **LOW** — retain as a narrow configuration adapter. |
| 15 | `infrastructure/composition_blocked_workflows.py` | 4 | `COMPOSITION` | 53 / 10 | complexity 1; effects 0; fan-out 4; 1 change | 1 / 1 | **LOW** — retain as a small blocked-workflow registry. |

## Decomposition order

1. **ARC-05 guardrails:** protect root entrypoints, installer boundaries, and
   composition direction before moving behavior.
2. **ARC-02 CLI:** extract `__main__.py` parsing, dispatch, consent, and
   rendering without changing workflow names, exit behavior, or safety gates.
3. **ARC-03 installer:** establish one installer application lifecycle owner,
   then extract process, host/filesystem, evidence, credential, and presentation
   adapters behind real ports.
4. **ARC-04 composition:** untangle `composition_runtime.py`,
   `composition_deployment.py`, `composition.py`, and the related capability
   modules using explicit dependency direction; preserve compatibility imports
   until consumers migrate.
5. **ARC-06 exceptions:** reduce the remaining mixed-boundary allowlist and
   attach an owner, rationale, and removal slice to every exception.

This ordering is driven by combined coupling, effects, lifecycle ownership,
change frequency, and test friction. It is not a descending line-count order.

## Resulting implementation order

The ranking feeds the remaining EPIC 03 work as follows:

| Priority | Follow-up issues / slices | Hotspots addressed | Completion guardrail |
|---|---|---|---|
| P0 | #362 / ARCH-03.19; #361 / ARCH-03.18 | `__main__.py`, `installer.py`, composition edge | Architecture checks and complexity guardrails fail on newly introduced root bypasses or uncontrolled growth. |
| P1 | #358 / ARCH-03.15 | `__main__.py` | CLI behavior and consent regression tests remain green. |
| P2 | #354 / ARCH-03.11; #353 / ARCH-03.10; #355 / ARCH-03.12; #360 / ARCH-03.17 | `installer.py`, `simple_installer.py` | One lifecycle owner; process, credential, result, redaction, and duplicate-path contracts remain deterministic. |
| P3 | #348 / ARCH-03.05; #351 / ARCH-03.08; #359 / ARCH-03.16 | composition runtime/platform/setup | Composition remains the concrete-binding owner and capability dependencies stay explicit. |
| P4 | #357 / ARCH-03.14; #364 / ARCH-03.21 | all remaining exceptions | Runtime-specific branching and resulting architecture documentation remain governed. |

Issue references above were confirmed against the open ARCH-03 backlog on
2026-09-13. They are sequencing inputs, not claims that those follow-up issues
are implemented by this inventory.

No live infrastructure command was run for this inventory.
