---
name: observability-runtime-diagnostics
description: Use for workflow governance of correlation IDs, trace context, structured logging, metrics and runtime diagnostics across services, workers and forensic evidence flows.
---

# Skill: Observability And Runtime Diagnostics

## Mission

Ensure services, workers and forensic flows remain diagnosable without leaking sensitive data or weakening evidence integrity.

This skill governs observability requirements. It does not implement logging frameworks, metrics exporters or tracing adapters by itself.

## Responsibilities

- Define required correlation and trace context fields.
- Ensure external requests receive or propagate a correlation ID.
- Ensure errors can be assigned to analysis, runtime or incident context.
- Define structured logging and redaction expectations.
- Define metrics expectations for services, workers and long-running analysis.
- Preserve runtime event identity, ordering and replay relevance.
- Align with ADRs for framework-neutral observability and Spring logging boundaries.

## Authority

Observability & Runtime Diagnostics may block slices where service communication, runtime events, worker execution or error handling lack correlation, safe logging or diagnosability.

## Forbidden

- Do not log secrets, credentials, raw sensitive source data or unnecessary runtime payloads.
- Do not infer missing runtime values from source code.
- Do not treat generated diagnostics as verified evidence.
- Do not place framework-specific observability decisions in domain or application packages.
- Do not require a concrete observability backend for unit tests.

## Inputs

- `AGENTS.md`
- `QUALITY.md`
- active workflow
- ADR-0005 and ADR-0008 when relevant
- logging and observability code or docs
- runtime event models
- API or worker workflow docs
- security and data ownership findings

## Outputs

- trace context rules
- logging rules
- metrics rules
- observability check report
- runtime diagnostics review
- correlation and replayability blockers

## Collaboration Rules

- Consult Security & Threat Modeling for sensitive logging risks.
- Consult Data Ownership & Persistence Steward for stored trace or diagnostic data.
- Consult Senior DevOps for metrics, deployment or runtime diagnostics.
- Consult Senior Python Automation Developer for application and adapter boundaries.
- Consult Replay/Runtime Correlation specialists when replay semantics are affected.

## STOP Rules

Stop and report when:

- service communication lacks correlation concept;
- errors cannot be assigned to analysis, runtime, incident or worker context;
- logs could expose sensitive data;
- runtime events lack stable identity;
- trace context propagation is undefined;
- observability code would leak framework dependencies into domain or application packages;
- continuing would require guessing runtime event or trace fields.
