---
name: devops-kubernetes
description: Use for Kubernetes material only after verifying that the repository contains Kubernetes manifests or deployment tooling.
---

# Kubernetes

## Purpose

Guide Kubernetes deployment material if such infrastructure is verified in the repository.

## Practices

- Verify existing manifests or deployment tooling before adding Kubernetes files.
- Keep secrets out of manifests and commits.
- Make resource, health-check and observability assumptions explicit.
- Keep runtime evidence storage and retention concerns documented.

## Verification

- Run available manifest validation or documented deployment checks.
- Do not invent Kubernetes commands when no verified tooling exists.
