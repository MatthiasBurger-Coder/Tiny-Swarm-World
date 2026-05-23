---
name: multipass-vm-provisioning
description: Use for Multipass VM provisioning guidance without running live VM commands.
---

# Multipass VM Provisioning

## Purpose

Guide Multipass VM provisioning automation and documentation while keeping live
VM creation out of normal development verification.

## Responsibilities

- Keep VM names, resources and lifecycle behavior explicit and configurable.
- Preserve command execution through ports and infrastructure adapters.
- Require mocks for VM operations in tests.

## Inputs

- VM configuration, command templates, provisioning services and tests.
- Root `AGENTS.md`, `QUALITY.md` and workflow scope.
- User provisioning requirement.

## Outputs

- Provisioning guidance, test needs and safety notes.
- STOP report when live VM behavior cannot be mocked.

## Boundaries

- Do not run `multipass` commands unless explicitly authorized.
- Do not embed host-specific absolute paths, usernames, IPs or secrets.

## STOP conditions

- VM lifecycle semantics are unclear.
- A change would execute commands at import or construction time.
- Verification would create, delete or mutate VMs.

## Collaboration with other skills

- Pair with `linux-host-preparation` and `network-topology-design`.
- Pair with `python-cli-automation` for command orchestration.
- Escalate architecture concerns to `hexagonal-architecture-expert`.

## Quality expectations

- Use mocked command tests for VM behavior.
- Run focused tests and relevant quality-gate subcommands.
