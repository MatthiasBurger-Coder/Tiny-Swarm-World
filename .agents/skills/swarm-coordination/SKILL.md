---
name: swarm-coordination
description: Use when explicitly coordinating multiple project subagents or roles for bounded, parallel work.
---

# Swarm Coordination

## Purpose

Coordinate multiple roles or agents when the user explicitly requests delegated or parallel work.

## Practices

- Decompose work into bounded, non-overlapping file ownership.
- Keep the critical path local unless a parallel side task can advance safely.
- Share exact contracts, files and expected outputs with each role.
- Integrate results through review, not blind acceptance.
- Stop when role findings contradict verified repository state.

## Verification

- Inspect git status before and after integration.
- Run targeted checks for each implemented slice.
