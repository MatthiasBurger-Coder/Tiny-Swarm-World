# ARCH-03.06 — Runtime Port and Docker Swarm Adapter

Status: implemented 2026-09-13

Issue: #349

## Decision

Deployment use cases depend on `PortSwarmStackRuntime`. The port exposes only
the proven operations required by current workflows: stack deployment, stack
and service inspection, and external-secret inspection/creation.

`DockerSwarmRuntime` is the infrastructure adapter for this port. It delegates
to the configured concrete transport (`LxcSwarmRuntime`) while keeping
managed-LXC shell details outside the application layer. Composition creates
both concrete objects and injects the adapter into application services.

## Failure semantics

Transport failures remain exceptions at the infrastructure boundary and are
translated or reported by the existing application workflow verification
paths. No raw Docker command output is added to the application port.

## Scope

This slice preserves the existing Docker Swarm behavior and does not add
Podman or Kubernetes adapters.
