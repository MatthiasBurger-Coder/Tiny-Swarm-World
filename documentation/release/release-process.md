# Release Process

Tiny Swarm World releases are controlled evidence baselines for a Linux/WSL-only
Python automation project. A release may describe repository readiness, and it
may describe live install readiness only when a matching redacted live evidence
package exists.

## Roles

| Role | Responsibility |
| --- | --- |
| Root Architect | Release scope, architecture risk, and final release decision. |
| Senior Tester | Quality-gate evidence and test baseline review. |
| Senior Documentation Engineer | Documentation baseline and changelog review. |
| Security Owner | Secret, evidence-redaction, dependency, and local admin-surface review. |
| Senior DevOps Engineer | CI status, branch protection, and artifact handling review. |

## Release States

| State | Meaning |
| --- | --- |
| Draft | Release scope is being assembled and may still change. |
| Candidate | Candidate branch, commit, and changelog are identified. |
| Evidence pending | Required evidence is incomplete, blocked, or under review. |
| Approved | Required evidence has been reviewed and release is authorized. |
| Released | Tag and release notes are published by an explicit release workflow. |
| Rejected | Candidate failed review or no longer represents the intended scope. |
| Superseded | A newer candidate replaces this release candidate. |

## Candidate Creation

Create a release candidate from a clean branch or commit that already passed the
required workflow checks. Do not create tags, upload artifacts, or distribute
packages from ordinary implementation workflows. A candidate must identify:

- source commit SHA and branch;
- intended version or project-specific release identifier;
- package metadata and changelog alignment with that intended version;
- included issues and pull requests;
- known limitations and deferred work;
- evidence paths or redacted summaries.

## Required Evidence

Before approval, collect:

- quality evidence from `python3 tools/quality_gate.py quality`;
- architecture evidence for changed boundaries, ADRs, or arc42 sections;
- security evidence for secrets, local admin surfaces, dependency and image risk;
- documentation evidence for operator-facing and governance changes;
- traceability evidence linking requirements, tests, and evidence;
- live evidence when the release claims live install readiness.

Live install readiness requires a redacted live run package that distinguishes
passed, blocked, refused, resource-gated, failed-to-apply, and failed-to-verify
states. A release must not claim live success from static tests alone.

## Approval And Tagging

The Root Architect approves release scope after quality, security, DevOps, and
documentation evidence are reviewed. Tagging is performed only by an explicit
release workflow. Tags must point to the approved commit and reference release
notes, evidence summaries, and known limitations.

## Post-Release Review

After release, record whether evidence remained reproducible, whether incidents
or regressions occurred, and whether CAPA or documentation updates are needed.
