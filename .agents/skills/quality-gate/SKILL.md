---
name: quality-gate
description: Identifies and executes the repository quality gate without weakening existing verification rules.
---

# Skill: Quality Gate

## Description
Identifies and executes the repository quality gate without weakening existing verification rules.

## Instructions
1. Read QUALITY.md.
2. Inspect Python tooling files.
3. Identify the correct quality-gate script.
4. Identify test, lint, typecheck, architecture, and validation commands.
5. Execute commands in the host-appropriate shell environment: use WSL on Windows hosts and native shell access on Linux hosts.
6. Stop and report if WSL is unavailable on Windows or cannot access the worktree.
7. For workflow execution, evaluate quality gates per workflow branch and per
   worktree; do not reuse evidence from another parallel workflow.
8. Keep test output and evidence files separate per workflow worktree unless
   the workflow explicitly defines a shared evidence artifact.
9. Serialize live validation when infrastructure is shared. Live LXD, LXC,
   Docker, Docker Swarm, networking, firewall, Portainer, Jenkins, SonarQube,
   Nexus, secrets-management, install, reset or reinstall validation may run in
   parallel only with an explicitly isolated live environment.
10. Run checks where feasible.
11. Summarize pass/fail results.
12. Report exact failing commands.

## Expected Inputs
- QUALITY.md
- tools/quality_gate.py
- requirements.txt
- setup.py
- .importlinter
- current diff

## Expected Outputs
- commands executed
- result summary
- failing checks
- suspected cause
- recommended next step

## Stop Conditions
Stop if:
- the documented quality gate is inconsistent with the Python tooling
- a command fails
- a test fails
- required tooling is missing
- thresholds would need to be changed
- architecture or test verification would need to be weakened
- quality evidence is shared across parallel workflow worktrees without an
  explicit workflow design
- live validation would mutate shared infrastructure concurrently
