# EPIC: Incremental SonarCloud remediation

Status: active

## Objective

Reduce verified open SonarCloud issues in Tiny Swarm World through small,
rule-specific remediation workflows. Each workflow must preserve product
behavior, test semantics, and the project's quality and architecture guards.

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

`workflow-sonarcloud-remediation-20260718` owns the baseline refresh and one
pilot batch of no more than 20 unambiguous `python:S3415` findings.

## Non-goals

This EPIC does not authorize live infrastructure operations, product behavior
changes, or a single bulk repair of all reported SonarCloud issues.
