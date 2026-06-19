# Final RabbitMQ Reference Classification

## Scan Source

The final scan was generated from tracked repository files with binary files excluded:

```bash
git ls-files -z | xargs -0 grep -nI -E "rabbitmq|RabbitMQ|RABBITMQ|amqp|AMQP|5672|15672"
```

The required recursive grep was attempted first, but the repository-wide
filesystem scan exceeded the local command timeout. The tracked-file scan is
the actionable source for committed product, test, documentation, and evidence
content.

## Summary

- RabbitMQ final references: 606 lines.
- Pulsar final references: 574 lines.
- Active runtime RabbitMQ references: none.
- Active configuration RabbitMQ references: none.
- Active deployment stack contract RabbitMQ references: none.
- Active compose stack RabbitMQ references: none.

## Migration Evidence

Classification: migration evidence.

Files:

- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/rabbitmq-reference-baseline.txt`
- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/pulsar-reference-baseline.txt`
- `.tiny-swarm/evidence/workflows/replace-rabbitmq-with-apache-pulsar/three-amigos-review.md`
- `.codex/evidence/slice-01-distribution.md`
- `.codex/evidence/slice-01-consolidation.md`
- `.codex/evidence/slice-02-distribution.md`
- `.codex/evidence/slice-02-consolidation.md`
- `.codex/evidence/slice-03-distribution.md`
- `.codex/evidence/slice-03-consolidation.md`
- `.codex/evidence/slice-04-distribution.md`
- `.codex/evidence/slice-04-consolidation.md`
- `.codex/evidence/slice-05-distribution.md`
- `.codex/evidence/slice-05-consolidation.md`
- `.codex/evidence/slice-06-distribution.md`
- `.codex/evidence/slice-06-consolidation.md`
- `.codex/evidence/slice-07-distribution.md`
- `.codex/evidence/slice-07-consolidation.md`
- `.codex/evidence/slice-08-distribution.md`
- `.codex/evidence/slice-08-consolidation.md`

These files intentionally describe the migration baseline, slice decisions,
removed RabbitMQ behavior, and validation history.

## Active Workflow Evidence

Classification: migration evidence.

Files:

- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`

These files are the workflow definition and generated workflow context for this
migration. They intentionally mention RabbitMQ as the source service being
replaced.

## Historical Workflow Documentation

Classification: historical documentation.

Files:

- `documentation/workflow/issues/issue-4/workflow.md`
- `documentation/workflow/issues/issue-63/workflow.md`
- `documentation/workflow/issues/issue-64/workflow.md`
- `documentation/workflow/issues/issue-65/workflow.md`
- `documentation/workflow/issues/issue-66/workflow.md`
- `documentation/workflow/issues/issue-67/workflow.md`
- `documentation/workflow/issues/issue-68/workflow.md`
- `documentation/workflow/issues/issue-69/workflow.md`
- `documentation/workflow/issues/issue-70/workflow.md`
- `documentation/workflow/issues/issue-71/workflow.md`
- `documentation/workflow/issues/issue-72/workflow.md`
- `documentation/workflow/issues/issue-73/workflow.md`
- `documentation/workflow/issues/issue-74/workflow.md`
- `documentation/workflow/issues/issue-75/workflow.md`
- `documentation/workflow/issues/issue-76/workflow.md`
- `documentation/workflow/issues/issue-77/workflow.md`
- `documentation/workflow/issues/issue-78/workflow.md`
- `documentation/workflow/issues/issue-80/workflow.md`
- `documentation/workflow/issues/issue-81/workflow.md`
- `documentation/workflow/issues/issue-82/workflow.md`
- `documentation/workflow/issues/issue-83/workflow.md`

These are issue-specific workflow records from before this migration. They are
not active runtime configuration or stack contracts.

## Historical Architecture Records

Classification: historical documentation.

Files:

- `documentation/architecture/agent-split-plan.md`
- `documentation/architecture/adr-service-access-dashboard-vaultwarden.adoc`
- `documentation/architecture/adr-separate-platform-artifacts-deployment.adoc`
- `documentation/architecture/adr-autonomous-setup-safety.adoc`

These documents record earlier architecture baselines and decisions. Current
runtime, deployment, setup, and service-access documentation was updated to
Apache Pulsar in Slice 08.

## Active Risk Comparison

Classification: deprecated compatibility note.

File:

- `documentation/arc42/11_risks_and_debt.adoc`

The remaining reference compares Pulsar's local resource footprint with the
previous RabbitMQ stack. It is an intentional risk note required by the
migration workflow, not an active service declaration.

## Bug Classification

No remaining RabbitMQ references are classified as bugs after Slice 09 cleanup.
The active install plan output and deployment workflow test fixtures were
updated from RabbitMQ to Apache Pulsar before this classification was recorded.
