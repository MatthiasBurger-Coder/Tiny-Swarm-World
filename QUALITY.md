# QUALITY.md

## Purpose

This file defines the local quality contract for Tiny Swarm World. It is the
authoritative source for verification commands used by workflow, agent, commit,
and push procedures.

Root `AGENTS.md` remains authoritative for architecture, safety, operating
model, and live-infrastructure restrictions.

## Runtime

- Run commands from the repository root.
- Use Linux or WSL. Do not use Windows-native command examples for normal
  development verification.
- Prefer `python3`.
- `tools/quality_gate.py` configures `PYTHONPATH=src` for its own checks.
- Manual Python commands still need `PYTHONPATH=src` when they import
  `tiny_swarm_world`.

## Build Tool Authority

Tiny Swarm World is a Python automation project. The Java code under
`src/main/java` and `pom.xml` are deployment-example surface and do not define
the default project quality gate.

Do not use Gradle, Maven, JUnit, ArchUnit, or Java dependency-verification
commands as the default workflow gate unless a task explicitly changes the Java
example application.

## Full Local Quality Gate

Run this before commit or push when practical, and for any change that affects
Python source, tests, architecture rules, quality policy, command construction,
YAML handling, path handling, repositories, or adapters:

```bash
python3 tools/quality_gate.py quality
```

This executes, in order:

- `lint`
- `arch-lint`
- `arch-tests`
- `typecheck`
- `test`

## Targeted Gates

Use the nearest meaningful gate during development:

```bash
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
```

For a focused unit test, run it with `PYTHONPATH=src`, for example:

```bash
PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
```

## Documentation And Governance Checks

For documentation-only or agent/workflow metadata changes, run:

```bash
git diff --check
```

For commit or push readiness, also run the full local quality gate when
practical. If the full gate is skipped for a documentation-only or
governance-only change, record the reason and do not claim it passed.

## Architecture Checks

The repository architecture checks are Python-based:

- `python3 tools/quality_gate.py arch-lint`
- `python3 tools/quality_gate.py arch-tests`

`arch-lint` requires `.importlinter` and the `lint-imports` executable.
`arch-tests` requires `tests.architecture.test_hexagonal_imports`.

## External Systems

The default quality gate must not create VMs, change networking, deploy Docker
stacks, or bootstrap local services. Mock command execution, network calls, VM
operations, and Docker operations unless the user explicitly requests a live
integration run.

## Failure Policy

- Failed required gates block commit and push.
- Missing required gate evidence blocks commit and push unless the skip is
  explicitly documented and justified.
- Do not lower thresholds, remove architecture rules, or weaken tests to make a
  gate pass.
- Report exact commands, results, and remaining blockers.
