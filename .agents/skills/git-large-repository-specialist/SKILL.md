---
name: git-large-repository-specialist
description: Use for Git checkout architecture, large repository performance, partial or shallow clone policies, sparse checkout, mirrors, and corruption recovery.
---

# Skill: Git Large Repository Specialist

## Description

Guides Git adapter and checkout planning for large repositories such as WildFly while preserving deterministic repository evidence.

## Instructions

1. Verify repository references, branch references, commit references, and checkout result contracts before proposing Git operations.
2. Keep Git as an outbound adapter behind an application or domain port.
3. Plan clone, fetch, branch checkout, commit checkout, current commit resolution, remote URL detection, and repository cleanup as explicit operations.
4. Treat monorepo handling, partial clone, sparse checkout, shallow clone, ref optimization, mirror strategies, detached head workflows, and branch resolution as policy-driven options.
5. Preserve exact commit identity, remote URL, branch input, checkout mode, elapsed time, and diagnostics in the checkout result.
6. Include repository corruption handling, timeout behavior, cancellation, retry boundaries, and safe `git gc` strategies.
7. Use WildFly as a hardening scenario for clone, checkout, source-root detection, metrics, timeout, and cleanup only.
8. Apply `.agents/skills/resilience-engineering/SKILL.md` for checkout timeouts, retry boundaries, cleanup-after-failure, dead-letter, diagnostics and graceful-degradation decisions.

## Expected Inputs

- repository URL and allowed protocol policy
- branch and commit references
- workspace path and lease
- timeout and large-repository policies
- mini repository and WildFly test scenarios

## Expected Outputs

- Git port operation plan
- Git adapter failure taxonomy
- large repository checkout strategy
- deterministic checkout result model
- WildFly hardening checklist

## Boundaries

- Do not execute parsers, Joern, BTM generation, graph engines, replay engines, or UI work as part of Git checkout.
- Do not run untrusted build scripts during checkout.
- Do not allow plugin-side Git behavior to replace server-side workspace preparation.

## Stop Conditions

Stop if:

- repository URL, branch, or commit identity cannot be validated;
- checkout would execute untrusted repository code;
- a cleanup operation could escape the workspace root;
- large-repository optimizations would make commit resolution unverifiable.
