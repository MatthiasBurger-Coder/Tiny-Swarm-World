---
name: network-topology-design
description: Use for Tiny Swarm World VM and Docker Swarm network topology planning.
---

# Network Topology Design

## Purpose

Guide network topology decisions for local VM and Docker Swarm automation while
keeping external mutations explicit and testable.

## Responsibilities

- Keep VM, host, Swarm, service and reverse-proxy network responsibilities
  distinct.
- Preserve deterministic configuration for ports, addresses and service names.
- Avoid host-specific IPs or secrets in committed configuration.

## Inputs

- Network configuration, compose files, docs and affected automation modules.
- Root `AGENTS.md`, `QUALITY.md` and workflow scope.
- Required service routing behavior.

## Outputs

- Network design notes, config impact and test guidance.
- STOP report when topology assumptions cannot be verified.

## Boundaries

- Do not run netplan, `socat`, Docker network or Swarm commands without explicit
  authorization.
- Do not place low-level network details in domain code.

## STOP conditions

- Required network facts are host-specific or unknown.
- Verification would mutate host or VM networking.
- A change crosses service stack boundaries without a workflow.

## Collaboration with other skills

- Pair with `multipass-vm-provisioning`.
- Pair with `swarm-volume-network-governance`.
- Pair with `reverse-proxy-routing` for routing behavior.

## Quality expectations

- Use structured configuration parsing and focused tests where behavior changes.
- Run `git diff --check` for documentation-only topology changes.
