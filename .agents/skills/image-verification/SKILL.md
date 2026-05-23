---
name: image-verification
description: Use for non-mutating container image verification guidance.
---

# Image Verification

## Purpose

Guide image verification expectations without turning Docker or registry access
into a default quality gate.

## Responsibilities

- Distinguish local metadata checks from live image inspection.
- Record when image verification is skipped due to absent Docker or registry
  access.
- Keep image evidence traceable to exact commands when executed.

## Inputs

- Image build/publish docs, registry docs and workflow scope.
- Available command output when verification is explicitly run.
- Root `QUALITY.md`.

## Outputs

- Verification plan, skipped-check rationale and risk notes.
- STOP report for unverifiable image assumptions.

## Boundaries

- Do not run Docker or registry commands unless explicitly requested.
- Do not claim an image exists without verified evidence.

## STOP conditions

- Required image evidence is unavailable.
- Verification would mutate a registry or host.
- A workflow requires image guarantees that cannot be checked.

## Collaboration with other skills

- Pair with `image-build-publish` and `image-versioning-tagging`.
- Pair with `platform-verification`.
- Pair with `registry-infrastructure`.

## Quality expectations

- Run `git diff --check` for governance changes.
- Report exact image commands only when they were actually executed.
