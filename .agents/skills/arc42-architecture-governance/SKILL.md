---
name: arc42-architecture-governance
description: Use for keeping arc42 architecture documentation synchronized with EPIC changes, ADRs, runtime behavior, deployment views, service boundaries, resilience decisions, architecture constraints, and verified implementation changes.
---

# Skill: arc42 Architecture Governance

## Purpose

Keep `documentation/arc42` aligned with verified requirements, architecture decisions, runtime behavior and workflows.

This skill updates architecture documentation. It does not create architecture decisions from guesses.

## Required Inputs

Inspect the relevant subset of:

- `AGENTS.md`
- `QUALITY.md`
- `documentation/epics`
- `documentation/arc42`
- `documentation/adr`
- `documentation/workflow`
- affected source, tests, schemas or examples
- affected skills and roles

## Update Triggers

Review arc42 when:

- EPIC assumptions change
- service boundaries change
- plugin versus server responsibilities change
- runtime behavior changes
- deployment topology changes
- persistence ownership changes
- UI communication strategy changes
- resilience decisions change
- scalability constraints change
- observability or audit requirements change
- architecture decisions are added, superseded or reinterpreted

## Section Mapping

Use the existing arc42 sections:

- `01-introduction-and-goals.md`: goals and stakeholder-facing quality needs
- `02-architecture-constraints.md`: non-negotiable constraints
- `03-system-scope-and-context.md`: boundaries and external systems
- `04-solution-strategy.md`: high-level architecture strategy
- `05-building-block-view.md`: components and responsibility ownership
- `06-runtime-view.md`: runtime behavior and communication paths
- `07-deployment-view.md`: deployment topology
- `08-crosscutting-concepts.md`: state integrity, security, observability and resilience
- `09-architecture-decisions.md`: ADR references
- `10-quality-requirements.md`: quality scenarios and verification expectations
- `11-risks-and-technical-debt.md`: known gaps and unresolved risk
- `12-glossary.md`: terminology

## ADR Propagation

ADRs record decisions and context. arc42 summarizes active architectural consequences. Workflows route implementation according to those consequences.

Do not rewrite ADR history or intent without an explicit architecture decision.

## Runtime And Deployment Rules

Document runtime or deployment changes when they alter:

- communication protocol
- service ownership
- process boundary
- storage boundary
- retry, timeout or degradation behavior
- health-check semantics
- deployment unit
- data retention or diagnostic handling

Always distinguish planned behavior from implemented behavior.

## Stop Conditions

Stop and report if:

- arc42 conflicts with the EPIC and the source of truth is unclear
- an ADR contradicts current implementation and the intended decision is unclear
- a service boundary moved without a documented architecture decision
- resilience behavior changed but no documentation owner is clear
- deployment assumptions changed but the deployment view cannot be updated from verified evidence
- continuing would require inventing architecture facts

## Expected Outputs

- arc42 update plan or patch
- ADR reference review
- architecture drift findings
- service-boundary notes
- resilience and deployment documentation notes
- unresolved conflicts
