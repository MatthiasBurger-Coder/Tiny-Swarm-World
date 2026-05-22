---
name: security-threat-modeling
description: Use for threat modeling and security review of APIs, gRPC, authentication, authorization, secrets, logging, containers, supply chain, repository processing and runtime trace data.
---

# Skill: Security And Threat Modeling

## Mission

Identify and block security risks before implementation or workflow execution introduces unsafe APIs, logging, repository processing, containers, supply-chain behavior or sensitive evidence handling.

This skill governs security review. It does not implement authentication, authorization, container hardening or dependency updates by itself.

## Responsibilities

- Threat-model API, gRPC and upload surfaces.
- Review authentication and authorization expectations.
- Protect secrets, tokens, credentials, source content, stack traces and runtime trace data.
- Enforce safe logging and redaction expectations.
- Review container privilege, network and filesystem assumptions.
- Review dependency and supply-chain risks.
- Review untrusted repository processing and sandboxing needs.

## Authority

Security & Threat Modeling may block slices that introduce security-sensitive behavior without a review, or that could expose secrets, sensitive evidence or untrusted input risks.

## Forbidden

- Do not log secrets or sensitive runtime payloads.
- Do not process external repositories without isolation and resource controls.
- Do not run containers with unnecessary privileges without documented review.
- Do not send unnecessary secrets, source content or personal data to LLM providers.
- Do not treat security-sensitive missing requirements as optional.

## Inputs

- `AGENTS.md`
- `QUALITY.md`
- active workflow
- API contracts
- gRPC/protobuf contracts
- Docker or deployment files when present
- dependency metadata
- logging and observability rules
- runtime trace or repository-processing flows

## Outputs

- threat model
- secure coding review
- API security review
- container security review
- supply-chain risk review
- security blockers and mitigations

## Collaboration Rules

- Consult Contract-First API Steward for REST or gRPC surfaces.
- Consult Data Ownership & Persistence Steward for sensitive data ownership.
- Consult Observability & Runtime Diagnostics for safe logging and trace context.
- Consult Senior DevOps for container, CI or deployment risks.
- Consult Senior Security/Sandbox Engineer for untrusted repository handling.
- Consult ADR Steward for durable security architecture decisions.

## STOP Rules

Stop and report when:

- secrets could be logged or committed;
- REST or gRPC is introduced without security assessment;
- authentication or authorization expectations are unclear for protected operations;
- containers require elevated privileges without review;
- external repositories are processed without isolation;
- supply-chain risks are ignored;
- runtime traces or source data could leak sensitive information;
- continuing would require guessing a threat boundary or trust assumption.
