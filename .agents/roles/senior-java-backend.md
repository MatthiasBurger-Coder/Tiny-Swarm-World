# Retired Java Project Structure Guard

## Responsibility

Stop and report when a request would reintroduce Java, Maven, Gradle, or Spring
Boot project structure into Tiny Swarm World without an explicit product-scope
change.

## Required Skills

- root `QUALITY.md` for repository-level verification

## Rules

- Do not let Java, Maven, Gradle, or Spring Boot structure drive the Python
  automation architecture.
- Do not route normal Tiny Swarm World domain, application, port, adapter, YAML,
  command, VM, network, or deployment automation work to this role.
- Use root `QUALITY.md` for the default repository quality gate.

## Outputs

- STOP report for out-of-scope Java/Maven/Spring Boot reintroduction.
- Verification notes for repository quality gates when governance text changes.
