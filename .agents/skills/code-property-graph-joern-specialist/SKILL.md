---
name: code-property-graph-joern-specialist
description: Use for Joern and Code Property Graph planning, data-flow, control-flow, taint analysis, graph traversal, semantic code analysis, and large project CPG handling.
---

# Skill: Code Property Graph Joern Specialist

## Description

Guides optional Joern and Code Property Graph work while keeping CPG generation and semantic analysis in project adapters.

## Instructions

1. Verify existing Joern adapter files, Docker configuration, semantic artifact models, and quality-gate expectations before planning changes.
2. Keep Joern, Code Property Graph, graph traversal, data-flow analysis, control-flow analysis, taint analysis, vulnerability modeling, and query optimization outside domain and application implementation details.
3. Treat large project CPG handling as optional and explicitly resource-bounded.
4. Preserve semantic code analysis outputs as evidence with provenance, artifact references, query version, diagnostics, and completeness state.
5. Keep Joern optional for the default quality gate unless repository documentation explicitly changes that.
6. Place Joern execution after workspace checkout and source-root detection, not in the plugin.
7. Use WildFly only as a later hardening candidate for workspace and Git first; do not run Joern for the current workspace/gRPC phase.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for Joern execution timeouts, bounded retries, cleanup, partial artifact handling, health checks and diagnostics decisions.

## Expected Inputs

- Joern adapter and Docker files
- semantic domain models
- source snapshot and workspace references
- CPG artifact storage contracts
- performance and security constraints

## Expected Outputs

- Joern/CPG responsibility review
- CPG artifact handling plan
- semantic analysis test strategy
- query optimization and large-project risk notes
- optional-integration quality gate guidance

## Boundaries

- Do not implement Joern execution or CPG analysis for the workspace/gRPC plan.
- Do not leak Joern APIs into domain or application.
- Do not treat static semantic relations as runtime execution evidence.

## Stop Conditions

Stop if:

- Joern artifacts cannot be linked to a verified source snapshot;
- CPG output would lose provenance or query version;
- optional Joern checks would become required for normal verification;
- plugin-side Joern execution is proposed.
