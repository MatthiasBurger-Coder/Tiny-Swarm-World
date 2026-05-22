---
name: security-sandbox-specialist
description: Use for untrusted repository handling, sandboxing, container isolation, filesystem restrictions, malicious build detection, secret leakage prevention, quotas, and safe Git operations.
---

# Skill: Security Sandbox Specialist

## Description

Guides secure handling of untrusted repositories and workspace execution boundaries.

## Instructions

1. Verify repository URL handling, workspace roots, Git adapter boundaries, and storage policies before proposing security controls.
2. Treat checked-out repositories as untrusted input by default.
3. Plan sandboxing, container isolation, filesystem restrictions, resource quotas, malicious build detection, safe Git operations, and cleanup safeguards.
4. Prevent secret leakage from repository contents, environment variables, runtime traces, logs, LLM prompts, and generated diagnostics.
5. Keep secure execution boundaries explicit. Do not run builds, parser plugins, scripts, hooks, or external tools unless the approved slice requires and isolates them.
6. Ensure workspace cleanup cannot escape server-owned roots.
7. Document risk handling for large public repositories such as WildFly before hardening runs.

## Expected Inputs

- Git and workspace workflow
- filesystem root policy
- secret and logging rules
- container or process execution requirements
- quality and CI constraints

## Expected Outputs

- sandbox boundary plan
- untrusted repository risk review
- safe Git operation checklist
- quota and cleanup recommendations
- security acceptance criteria

## Boundaries

- Do not execute untrusted build scripts for the workspace/gRPC phase.
- Do not send repository content or secrets to LLM providers.
- Do not add networked services, telemetry, or secret-dependent tooling without approval.

## Stop Conditions

Stop if:

- workspace path validation is unclear;
- cleanup or Git operations could affect paths outside the workspace;
- credentials, tokens, or sensitive data appear in planned artifacts;
- sandbox assumptions are not testable or documented.
