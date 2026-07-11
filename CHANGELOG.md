# Changelog

All notable changes are recorded here. Release publication still requires the
governed release process and its evidence; entries under Unreleased are not a
release claim.

## [Unreleased]

### Fixed

- Fail closed when a required managed-secret consumer is not configured.
- Move secret configuration and evidence file access behind an application
  port and infrastructure adapter.

### Changed

- Record the explicit non-interactive live-consent architecture decision.
- Align Python, dependency-lock, skill-registry, and release metadata.

### Security

- Add explicit dependency-audit and local SBOM policy without weakening the
  non-mutating default quality gate.
- Enable TLS certificate verification by default for Infisical bootstrap HTTP
  calls and remove secret-bearing file-content logging.
- Pin managed image defaults, remove the Jenkins root override, and retire the
  direct Nexus helper that changed the host Docker daemon outside CLI consent.

## [0.2.0] - 2026-06-12

- Stabilized the governed live Linux installer baseline. Detailed evidence and
  limitations remain attached to the release and repository history.

[Unreleased]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/compare/0.2.0...HEAD
[0.2.0]: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/releases/tag/0.2.0
