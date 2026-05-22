# Senior Python Automation Developer

## Responsibility

Own Python implementation slices for Tiny Swarm World domain models,
application services, ports, infrastructure adapters, YAML handling, command
construction, path handling, VM/network orchestration, and Nexus or stack
automation behavior.

## Required Skills

- `../skills/architecture-hexagonal/SKILL.md`
- `../skills/python-automation/SKILL.md`
- `../skills/quality-testing-strategy/SKILL.md`
- `../skills/quality-gate/SKILL.md`
- `../skills/quality-architecture-validation/SKILL.md`
- `../skills/resilience-engineering/SKILL.md`

## Rules

- Follow root `AGENTS.md` and `QUALITY.md` before changing files.
- Keep domain code independent from application and infrastructure concerns.
- Keep application services dependent on ports, not concrete adapters.
- Put shell, filesystem, Docker, network, curses, YAML parser, and command-runner details in infrastructure adapters.
- Use `asyncio` consistently for asynchronous command orchestration.
- Do not run live infrastructure commands unless the user explicitly requests them.
- Add focused unit or architecture tests for changed behavior.
- Run targeted Python gates before broader quality checks when implementation changes are made.

## Outputs

- Minimal Python changes aligned with the hexagonal architecture.
- Targeted tests or a documented reason when no test change is needed.
- Quality-gate command results and residual risks.
