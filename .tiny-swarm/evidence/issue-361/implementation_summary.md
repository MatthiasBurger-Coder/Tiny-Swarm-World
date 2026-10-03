# Issue #361 implementation summary

The source-only AST checker records physical size, a McCabe-style branching
indicator, direct import fan-out, and exact cross-module orchestration copies
for package-root modules, all application services, composition modules, and
infrastructure adapters. Its committed JSON snapshot is the current
baseline. New or materially grown combinations of complexity and coupling fail
the canonical quality gate; existing hotspots remain visible for EPIC #313.

`tools/quality_gate.py quality` runs the check before lint, architecture,
typecheck, and tests. The existing GitHub Python Quality Gate job runs that
canonical command on pull requests. `QUALITY.md` and the architecture analysis
document describe the command, metrics, review triggers, known limitations,
and exception policy. The exception map is empty. Updating `QUALITY.md`
required refreshing its SHA-256 entry in the skill registry's governing hash
cache.

Architecture review found that a narrower first discovery rule omitted some
application owners. The final rule covers all application services and adapters, and flags
disappearing baseline paths. Product workflows and live infrastructure behavior
were not changed.
