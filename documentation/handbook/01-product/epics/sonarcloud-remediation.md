# EPIC: Incremental SonarCloud remediation

Status: active

## Objective

Resolve the complete, frozen baseline of 329 verified open SonarCloud issues
through small, rule-specific remediation batches. Each batch must preserve
product behavior, test semantics, and the project's quality and architecture
guards; the overall EPIC is complete only when every baseline issue key has
remote SonarCloud resolution evidence.

## Requirement authority

The requester-provided SonarCloud project issue view and the public SonarCloud
issue API are the issue inventory source. This EPIC is the repository-local
traceability authority for workflows derived from that inventory.

## Constraints

- Do not use bulk text replacement, quality-profile changes, suppressions, or
  test exclusions as remediation.
- Keep batches bounded, with concrete issue keys and source locations recorded
  before editing.
- Treat each Sonar rule family as a separate remediation concern.
- Changes outside tests require a successor workflow with explicit architecture
  review.
- Run the relevant local quality gates and obtain remote branch-analysis
  evidence before a batch is called complete.

## Current delivery slice

`workflow-sonarcloud-remediation-20260718` owns the complete remediation
program: baseline refresh, eleven `python:S3415` batches of at most 20 issues,
ten `python:S5778` batches of at most 10 issues, and one bounded batch for
each remaining rule family. Every baseline issue key must be assigned exactly
once; a blocked key remains explicit and prevents an EPIC DONE claim.

## Non-goals

This EPIC does not authorize live infrastructure operations, product behavior
changes, a blind bulk edit, suppressions, test exclusions, or quality-profile
changes. A source or architecture change outside the manifest-listed repair
scope stops the batch for an explicit successor workflow and review.
