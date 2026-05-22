---
name: performance-scalability-engineer
description: Use for memory profiling, large AST and repository handling, parallel analysis, CPU pressure, scan optimization, async or batch execution, streaming processing, and instrumentation.
---

# Skill: Performance Scalability Engineer

## Description

Guides performance and scalability planning for large repositories and long-running analysis jobs.

## Instructions

1. Verify the current repository modules, quality gates, and planned slice before adding performance requirements.
2. Plan memory profiling, CPU pressure handling, repository scan optimization, async execution, batch processing, streaming processing, and performance instrumentation.
3. Treat large AST handling and parser execution as later analysis work unless the current approved slice explicitly includes it.
4. Define measurable baselines for checkout time, workspace size, file count, source-root detection time, cleanup time, and failure behavior.
5. Use WildFly performance baseline only for Git/workspace hardening in the current phase.
6. Keep performance metrics deterministic enough for comparison, but avoid brittle timing assertions in unit tests.
7. Document resource limits, timeouts, concurrency boundaries, and backpressure signals.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for timeout budgets, bulkheads, circuit breakers, degraded behavior, cleanup and retry-observability decisions.

## Expected Inputs

- workspace and Git workflow
- large repository scenarios
- Python tooling and CI constraints
- quality-gate runtime expectations
- system resource constraints

## Expected Outputs

- performance risk assessment
- scalability test plan
- WildFly measurement plan
- resource quota and timeout recommendations
- instrumentation notes

## Boundaries

- Do not run parser, Joern, BTM, graph, replay, or UI performance tests for the current workspace/gRPC phase.
- Do not weaken tests or quality gates for speed.
- Do not add telemetry or external services without explicit approval.

## Stop Conditions

Stop if:

- performance goals require unverified infrastructure;
- test design would be nondeterministic or environment-fragile without documented tolerance;
- resource usage could exhaust local or CI environments without safeguards;
- measurements would require executing untrusted repository code.
