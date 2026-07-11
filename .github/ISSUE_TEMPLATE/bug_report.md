---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the infrastructure automation bug**
A concise description of the failed workflow or incorrect state.

**Workflow and command**
Provide the workflow name and POSIX command. Redact passwords, tokens, local
addresses, user names, and private paths.

**Environment**
- Runtime: native Linux or WSL2
- Distribution and version:
- Python version:
- Incus version and backend:
- Tiny Swarm World commit:

**Observed result**
Include the status (`refused`, `blocked`, `failed_to_apply`, or
`failed_to_verify`) and a redacted evidence summary. Do not attach `.env`
files or raw secret-bearing logs.

**Expected result**
Describe the verified state you expected.

**Live mutation**
State whether live infrastructure commands were run and whether the target is
disposable or recoverable.

**Additional context**
List relevant configuration keys by name only and any safe recovery attempted.
