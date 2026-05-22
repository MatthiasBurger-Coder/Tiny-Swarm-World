---
name: python-automation
description: Use for Tiny Swarm World Python automation changes in domain, application services, ports, infrastructure adapters, YAML handling, command orchestration, path handling, and VM/network/deployment automation.
---

# Python Automation

## Purpose

Guide Python implementation work while preserving Tiny Swarm World's
hexagonal architecture and Linux/WSL-only operating model.

## Rules

- Read root `AGENTS.md` and `QUALITY.md` before changing files.
- Keep domain code free from infrastructure, command runners, YAML parsers,
  UI adapters, Docker details, logging setup, and dependency injection.
- Keep application services dependent on ports and domain objects, not concrete
  infrastructure adapters.
- Keep concrete shell, filesystem, Docker, network, curses, YAML, logging, and
  external-client details inside infrastructure adapters.
- Use `asyncio` consistently for asynchronous command orchestration.
- Do not run live infrastructure commands unless the user explicitly requests
  live changes.
- Use structured YAML APIs or existing YAML adapter helpers for configuration
  changes.

## Verification

Run the nearest meaningful gate first:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
```

For architecture-sensitive changes, also run:

```bash
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
```

Before commit or push, run the full gate when practical:

```bash
python3 tools/quality_gate.py quality
```

## Stop Conditions

Stop when a command template, YAML key, path rule, adapter boundary, live
infrastructure side effect, or required test target cannot be verified.
