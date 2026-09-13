# Implementation Summary — #346 / ARCH-03.03

This issue adds a source-level orchestration hotspot inventory and ranking. It
does not refactor product code or execute live infrastructure.

The result records:

- the complete current orchestration-edge scope;
- repeatable AST and Git measurements;
- weighted ranking criteria and severity rules;
- all 15 scoped surfaces with LOW/MEDIUM/HIGH/CRITICAL classification;
- decomposition targets for every HIGH/CRITICAL result;
- the P0–P4 order for ARC-02 through ARC-06 follow-up work.

The ranking confirms `installer.py` as CRITICAL, followed by `__main__.py` and
`composition_runtime.py` as the primary HIGH hotspots. The composition facade
is also HIGH because its compatibility refresh cycle and change frequency make
it difficult to isolate, despite low local branching complexity.
