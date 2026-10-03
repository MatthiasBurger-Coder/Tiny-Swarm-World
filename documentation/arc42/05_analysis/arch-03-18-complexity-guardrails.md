# ARCH-03.18 — Complexity and maintainability guardrails

Issue: #361. Parent: #313. Baseline captured on 2026-10-03 from the clean
`main` source before this guardrail changed product code. The machine-readable
snapshot is `arch-03-18-complexity-baseline.json`; the reviewed exception list
is `arch-03-18-complexity-exceptions.json`.

## Original baseline and covered scope

The static checker covers every package-root Python module, every
`infrastructure/composition*.py` module, every application service module, and
all infrastructure adapters. This includes future owners reached by
orchestration decomposition and provider, preflight, and Swarm runtime adapters
that already orchestrate external work. It reads source only. The original snapshot
included 259 modules and 1,955 functions. The largest measured modules are
`installer.py` (1,819 lines, complexity indicator 231, import fan-out 38),
`adapters/clients/lxc_node_provider.py` (1,804 lines, indicator 226, fan-out
19), and `composition_runtime.py` (1,774 lines, indicator 80, fan-out 84).
These describe the original captured candidate, not the extracted current
installer. They were existing debt, not a new failure.

Seventeen functions meet the critical function combination at baseline: at least 15
branch paths and 60 lines. They include `installer._run_prepared` (24 / 233),
`composition_deployment.build_lxc_deployment_services` (44 / 314), and
`platform/workflow/runtime._run_mutating_steps` (37 / 91). The complete list,
class sizes and complexities, module sizes, fan-out, and duplicate fingerprints
are in the snapshot. No exact cross-module orchestration duplicates met the
checker's complexity and size filter at baseline. This does not claim there is
no semantic duplication; ARCH-03.17 documents the reviewed duplicate paths.

## Metric method

`python3 tools/quality_gate.py complexity` parses Python ASTs without importing
or executing product modules. The function complexity indicator starts at one
and counts `if`, loops, conditional expressions, exception handlers, assertions,
boolean edges, comprehensions, and non-default `match` cases. It is a
McCabe-style source indicator, not a precise control-flow graph measurement.
Class complexity sums direct method indicators. Module complexity sums function
branch additions. Import fan-out counts distinct direct import targets. Lines
are physical source spans. Duplicate orchestration uses exact normalized AST
fingerprints across modules for functions with complexity at least eight and
span at least 12 lines; it catches literal copied flows and can miss equivalent
flows expressed differently.

Run `python3 tools/check_complexity_guardrails.py --show-current` to inspect a
fresh snapshot. Baseline updates require a reviewed architecture change that
explains why the new structure is acceptable. Do not regenerate the baseline
solely to clear a failed check.

## Review triggers

The canonical local quality gate runs this check, so the Python Quality Gate
pull-request job fails for unreviewed findings. Size alone never fails. A new
function triggers review when it combines at least 15 branch paths with at
least 60 lines; an existing critical function triggers when complexity grows
by four, or by two with at least 40 additional lines. A new class triggers at
25 summed method paths and 120 lines; an existing class triggers at eight new
paths while at least 120 lines. A new module triggers at 40 paths, 12 import
targets and 300 lines. Existing module growth triggers at ten new paths plus
three new import targets, or at 25 new paths or eight new import targets alone.
A newly copied qualifying orchestration function
across modules also triggers. An existing function, class, or module that first crosses
its critical combination triggers review even when the final increment is small.

Disappearance of a covered baseline module also triggers review, so moving an
entrypoint or service cannot silently shrink coverage. The coverage rule picks
up new files in the listed areas automatically.

These combinations are review signals for accumulating behavior and coupling
at an architectural boundary. They do not prescribe maximum file or function
lengths, and a long cohesive function does not fail merely for being long.
Existing hotspots are retained as a named baseline for the decomposition work
in EPIC #313. The check does not decide whether a refactor is safe; focused
behavior and architecture tests remain required.

## Exception policy

The current reviewed exception map is empty. If a finding is intentionally
accepted, add its exact finding key to the JSON map with `owner`, `reason`,
and tracking `issue`. The pull-request review then has a small, explicit
architecture decision to inspect. The checker rejects incomplete or stale
exceptions. Remove an exception when the finding disappears. A baseline update
or exception must not conceal a new dependency bypass or weaken the existing
hexagonal architecture checks.

Local verification is `APPLICABLE_LOCAL`. Live installation and browser checks
are `NOT_APPLICABLE`. SonarQube is `APPLICABLE_EXTERNAL` to publication, and
no external result is claimed by this local implementation evidence.

## Reviewed EPIC 03 ownership relocation (2026-10-03)

ARC-02 moves CLI parsing, dispatch and rendering to canonical CLI adapters;
ARC-03 moves installer orchestration to three application owners with six
consumed ports and technology helpers to focused installation adapters. Root
installer bodies delegate; root exports preserve import compatibility.

The corresponding baseline update is restricted to these changed/new owners.
It records measured final metrics rather than regenerating unrelated entries.
Existing CLI rendering is a canonical relocation; installer helper complexity
is attributed to its concrete owner. No thresholds or exception policy change.
Unrelated module/function/class baselines remain unchanged.

The ownership map in `arch-03-01-responsibility-ownership.md` and the EPIC
completion evidence provide before/after attribution. New responsibilities
remain subject to the same growth checks, architecture mutation probes and
behavioral regression gate. Local verification does not establish live or
external success.
