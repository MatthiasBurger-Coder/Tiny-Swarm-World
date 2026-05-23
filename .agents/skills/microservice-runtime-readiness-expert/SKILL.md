---
name: microservice-runtime-readiness-expert
description: Use to verify whether a candidate service is independently buildable, startable, testable, configurable, observable, health-checkable, and container-ready before it is called a microservice.
---

# Skill: Microservice Runtime Readiness Expert

## Mission

Verify runtime independence for candidate services before documentation,
workflows or implementation slices call them microservices.

This skill reviews readiness evidence. It does not create service scaffolds,
Dockerfiles, Kubernetes manifests, Docker Swarm descriptors, CI workflows or
deployment scripts.

## Core Rule

A service is not a microservice until it can be built, started, tested,
configured, observed, health-checked and containerized independently from other
services.

Docker, Docker Swarm and Kubernetes readiness must be verified from repository
tooling before commands, manifests or deployment claims are documented.

## Responsibilities

- Verify the candidate service has its own build entry point or documented
  build path.
- Verify the candidate service has an independent start command.
- Verify configuration, ports, environment variables and secrets are explicit.
- Verify healthcheck, readiness and liveness expectations when runtime
  deployment is in scope.
- Verify logging, metrics, tracing and correlation expectations.
- Verify unit, contract, integration and runtime-start tests expected for the
  slice.
- Verify Docker image readiness only from existing or explicitly added
  Dockerfile evidence.
- Treat Docker Swarm and Kubernetes as readiness targets that require verified
  repository manifests or tooling before commands are documented.
- Block direct Java class coupling between services.

## Verified Repository Context

Current repository inspection found Dockerfiles for existing Boot App, Joern and
UI surfaces, but no verified Docker Swarm or Kubernetes manifests for
microservice deployment. Future readiness reviews must re-check the repository
before documenting deployment commands.

## Runtime Readiness Record

Return a concise record with:

- candidate service
- build command or build path
- start command
- configuration source
- exposed ports
- secrets handling
- healthcheck readiness
- observability readiness
- Dockerfile evidence
- Docker Swarm evidence
- Kubernetes evidence
- test commands
- missing evidence
- required reviewers
- decision: `READY`, `NOT_READY` or `REQUIRES_REFINEMENT`

## Collaboration Rules

- Consult Senior System Architect and Service Decomposition And Bounded Context
  for service autonomy.
- Consult Senior DevOps Engineer for Python tooling, Docker, CI/CD and deployment
  concerns.
- Consult DevOps Docker only after Docker files or Docker workflows are
  verified.
- Consult DevOps Kubernetes only after Kubernetes manifests or tooling are
  verified.
- Consult Senior Tester for runtime-start and quality-gate expectations.
- Consult Observability Runtime Diagnostics for logging, metrics, tracing,
  correlation IDs and redaction.
- Consult Security Sandbox Specialist for container isolation, secrets and
  untrusted repository handling.

## Forbidden

- Do not claim a service is independently runnable without a verified start
  command.
- Do not claim a service is independently buildable without a verified build
  path.
- Do not claim Docker readiness without Dockerfile or documented image-build
  evidence.
- Do not claim Docker Swarm or Kubernetes readiness without verified repository
  tooling or manifests.
- Do not invent ports, environment variables, healthcheck endpoints, container
  commands, deployment descriptors or CI jobs.
- Do not allow direct Java class dependencies between services.
- Do not make optional external infrastructure part of the default quality gate
  unless `QUALITY.md` or the workflow explicitly requires it.

## STOP Rules

Stop and report when:

- build or start commands cannot be verified;
- configuration, port or secret handling is unclear;
- healthcheck, readiness or liveness behavior is claimed without evidence;
- Docker, Swarm or Kubernetes commands would need to be invented;
- runtime-start tests or quality gates are missing for runtime-affecting work;
- a candidate service depends on another service's Java implementation classes;
- observability or correlation expectations are required but undefined;
- continuing would require guessing deployment tooling, runtime commands,
  healthcheck endpoints, environment variables, ports or service dependencies.
