# Changelog Policy

The changelog explains what changed, why it matters, and which evidence supports
release claims. It is not a substitute for tests, live evidence, or audit
records.

## Categories

- Added: new behavior, documentation, configuration, or governance capability.
- Changed: behavior or process changed without removal.
- Fixed: defect or regression correction.
- Removed: deleted behavior, files, commands, or support surface.
- Security: secret handling, threat model, dependency, image, or admin-surface change.
- Documentation: operator, architecture, workflow, or governance documentation.
- Governance: QMS, ISMS, audit, traceability, branch, CI, release, or skill rules.
- Known limitations: verified gaps, unverified live behavior, or deferred work.

## Required PR Information

Each release-relevant PR should provide a summary, changed areas, validation
commands and results, live-command statement, known limitations, and related
issues. Security-sensitive PRs must include a redaction and secret-leakage
statement. Documentation-only PRs must not claim behavior was implemented unless
the repository code or configuration actually changed.

## Versioning

Tiny Swarm World uses semantic version tags. Package metadata must match the
latest released tag until an explicit release workflow approves and publishes
the next version. Release notes also identify the Git commit SHA and release
candidate branch.

Breaking changes include removed command flags, changed config keys, changed
secret source semantics, changed live-consent rules, changed service topology,
or changed supported runtime assumptions. Live-readiness claims must reference a
matching live evidence baseline and list any resource-gated or blocked checks.
