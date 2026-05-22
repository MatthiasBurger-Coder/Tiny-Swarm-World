---
name: quality-mutation-testing
description: Use for mutation-testing guidance after verifying that the repository has documented mutation tooling.
---

# Mutation Testing

## Purpose

Use mutation testing guidance to strengthen critical logic when the repository has verified tooling for it.

## Practices

- Apply mutation testing to high-value domain, evidence and replay rules.
- Verify that mutation tooling exists before referencing commands.
- Do not introduce mutation tooling as part of unrelated changes.
- Treat surviving mutants as prompts for clearer behavior tests.

## Verification

- Run only repository-documented mutation commands.
- Report when mutation testing is not configured.
