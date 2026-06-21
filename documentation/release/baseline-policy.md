# Baseline Policy

Baselines are reviewed snapshots used to reproduce and audit a release,
workflow, or operational claim. Repository files remain the committed baseline;
ignored local evidence may be referenced only by redacted summaries.

| Baseline | Required Files Or Artifacts | Evidence Source | Owner | Review | Retention |
| --- | --- | --- | --- | --- | --- |
| Source | Git commit SHA, branch, changed source paths | Git history and PR diff | Root Architect | Architecture and test review when behavior changes | Retain through Git history |
| Documentation | README, `documentation/**`, ADRs, workflow docs | Documentation diff and navigation links | Senior Documentation Engineer | Documentation consistency review | Retain in repository |
| Configuration | `infra/config/**` and compose stack definitions | Config diff, parser tests, contract docs | Senior DevOps Engineer | Safety and redaction review | Retain in repository |
| Test | Unit, architecture, integration-safe tests | `python3 tools/quality_gate.py quality` output | Senior Tester | Gate result review | Retain as PR evidence summary |
| Security | Security docs, secret handling rules, scan policies | Security review and redaction evidence | Security Owner | Risk and incident-process review | Retain in security docs and PR evidence |
| Live evidence | Redacted run template, checksums, pass/fail table | Ignored `.tiny-swarm-world/evidence/**` summarized safely | Senior DevOps Engineer | Redaction and live-result review | Retain local package or approved secure store |
| Release artifact | Tag, release notes, optional distribution artifact | Release workflow evidence | Root Architect | Release approval review | Retain according to release notes |

Ignored local evidence, local `.env` files, raw logs, screenshots, and secret
material must not be committed when they contain local or sensitive data. They
may be referenced by a redacted summary that records classification, checksum,
status, and location without exposing private values.

No baseline may convert missing evidence into a pass. Missing, blocked,
resource-gated, refused, failed-to-apply, and failed-to-verify states remain
explicit until a later workflow collects valid evidence.
