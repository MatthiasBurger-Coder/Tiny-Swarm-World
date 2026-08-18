# Workflow Context Pack: Issue #252

Workflow version: issue-252-classic-public-beta-rc1-20260818
Workflow path: documentation/workflow/workflow.md
Requirement baseline: documentation/workflow/requirement-matrix.md
Authoring branch: docs/workflow-issue-252-ci-live-addendum-20260818
Planned execution branch: release/classic-public-beta-rc1-stabilization
Status: AUTHORED_NOT_EXECUTED

## Process

- Process strand: issue -> requirement matrix -> Three-Amigos -> asset inventory -> local tests -> CI gates -> explicit live evidence -> completion audit
- Execution profile: FULL_PATH
- Issue: GitHub #252, RC1 Classic Profile Stabilization / Public Beta Acceptance
- Current baseline: current main commit, verified before authoring branch creation
- Live state authority: documentation/process/verification-state-policy.md
- Completion authority: documentation/process/issue-completion-discipline.md

## Affected areas

- Linux and WSL2 host classification, filesystem and Incus readiness
- Managed Incus/LXC nodes, Docker Engine and Docker Swarm
- Routing, Service Access, Infisical/secrets, artifacts and configured services
- Python hexagonal automation and deterministic acceptance tests
- Live/browser/API evidence, redaction, checksums and RC1 release decision
- GitHub Actions quality/compatibility/Sonar workflows and self-hosted Classic
  live runner qualification

## Forbidden or gated areas

- Podman, Kubernetes, alternate runtime and new orchestration abstractions
- Java, Maven, Spring Boot and Windows-native project execution
- Administrator PowerShell privilege escalation by workflow automation
- Incus, Docker, Swarm, compose, networking, bootstrap and credential-backed
  live mutation without explicit per-invocation consent
- Raw credentials, tokens, authorization headers, full environment files and
  unredacted sensitive evidence
- RC1 acceptance from static tests, planned commands, skipped or partial runs
- CI workflow presence without real run evidence
- GitHub-hosted runner substituted for a verified Classic-capable self-hosted
  runner

## Required roles

- Senior Requirement Engineer
- Senior System Architect
- Senior Python Automation Developer
- Senior Tester
- Senior Workflow Architect
- Issue Completion Auditor

## Conditional roles

- Senior DevOps for runtime, deployment and live host work
- Live Evidence Validation Expert for redaction, checksums and live states
- Senior Documentation Engineer for workflow/Arc42 synchronization
- Release Baseline Governance Expert for the final release decision
- Console/status UI reviewer only if terminal status/progress behavior changes

## Quality commands

Run from Linux/WSL with POSIX paths:

- git diff --check
- python3 tools/quality_gate.py lint
- python3 tools/quality_gate.py arch-tests
- python3 tools/quality_gate.py typecheck
- python3 tools/quality_gate.py test
- python3 tools/quality_gate.py quality

The full local gate is not live, browser, SonarQube or release evidence.

## Slice order

S252-01 -> S252-02 -> S252-03
S252-03 -> S252-04 -> S252-05 -> S252-06 -> S252-07
S252-03 -> S252-08 -> S252-09 -> S252-10
S252-03 -> S252-13 -> S252-14 -> S252-15 -> S252-16
S252-07, S252-10 and S252-16 -> S252-11 -> S252-12

Live slices are serialized. Each executable slice requires distribution and
consolidation evidence under .codex/evidence/.

## Hashes

The JSON context pack contains SHA-256 hashes for governing files. It is stale
when a governing hash changes, when workflow/requirements/architecture scope
changes, or when a conflict is discovered. The repository files remain the
source of truth; this pack is only navigation and preflight context.
