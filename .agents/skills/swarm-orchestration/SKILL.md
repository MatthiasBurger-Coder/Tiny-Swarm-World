---
name: swarm-orchestration
description: Converts a complex task into a Codex-local multi-agent workflow using read-only reviewers, one orchestrator, and one sequential implementation worker.
---

# Skill: Swarm Orchestration

## Description
Converts a complex task into a Codex-local multi-agent workflow using read-only reviewers, one orchestrator, and one sequential implementation worker.

## Instructions
1. Read the user task.
2. Read AGENTS.md.
3. Read QUALITY.md.
4. Read the active workflow file.
5. Assign read-only review concerns to the matching Codex agents.
6. Consolidate findings into slices.
7. Ensure only implementation_worker modifies files.
8. Define verification commands for each slice.
9. Do not add external orchestration frameworks, MCP servers, hooks, or background workers.

## Expected Inputs
- user task
- AGENTS.md
- QUALITY.md
- active workflow file
- relevant repository files
- read-only agent findings

## Expected Outputs
- orchestration plan
- ordered slices
- agent responsibility map
- verification plan
- risks and stop conditions

## Stop Conditions
Stop if:
- repository rules contradict the task
- a required file cannot be found
- the task requires external runtime integration not explicitly approved
- two write-capable workers would be needed concurrently
