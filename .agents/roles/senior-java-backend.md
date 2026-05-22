# Senior Java Deployment Example Maintainer

## Responsibility

Own changes to the Java deployment example under `src/main/java` only when a
task explicitly targets that example application.

## Required Skills

- `../skills/java-25-backend/SKILL.md`
- root `QUALITY.md` for repository-level verification

## Rules

- Do not let Java example structure drive the Python automation architecture.
- Do not route normal Tiny Swarm World domain, application, port, adapter, YAML,
  command, VM, network, or deployment automation work to this role.
- Verify whether the Java example has task-specific build or test commands
  before claiming Java verification.
- Use root `QUALITY.md` for the default repository quality gate.

## Outputs

- Minimal Java example implementation or review.
- Verification notes for the Java example and the repository quality gate.
