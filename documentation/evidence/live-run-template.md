# Live Run Evidence Template

Copy this template into the ignored run directory. Replace placeholders only
with redacted summaries. Never paste raw command output, environment files,
tokens, passwords, private keys or join credentials.

```yaml
run_id: "<unique-id>"
repository_commit: "<commit-sha>"
scenario: "A_fresh_install|B_reconcile_rerun|C_existing_update"
host:
  class: "native_linux|wsl2"
  target_id: "<redacted-label>"
  consent_state: "LIVE_CONSENT_MISSING|LIVE_VERIFIED|..."
  consent_reference: "<approval-record-reference>"
started_at_utc: "<timestamp>"
finished_at_utc: "<timestamp>"
phases:
  - id: preflight
    state: "<policy-state>"
    attempts: 0
    evidence: []
    summary: "<redacted-summary>"
  - id: nodes_docker_swarm_network_traefik
    state: "<policy-state>"
    attempts: 0
    evidence: []
    summary: "<redacted-summary>"
  - id: secrets_artifacts_and_services
    state: "<policy-state>"
    attempts: 0
    evidence: []
    summary: "<redacted-summary>"
  - id: readiness_and_browser
    state: "<policy-state>"
    attempts: 0
    evidence: []
    summary: "<redacted-summary>"
cleanup:
  state: "<policy-state>"
  summary: "<redacted-summary>"
checksums_manifest: "checksums.sha256"
review:
  reviewer: "<role-or-redacted-id>"
  reviewed_at_utc: "<timestamp>"
  decision: "PASS|INCOMPLETE|BLOCKED|REJECTED"
  findings: []
```

## Evidence file naming

Use stable, non-sensitive names such as `run-summary.yaml`,
`phase-preflight.yaml`, `phase-readiness.yaml`,
`traefik-admin-summary.yaml`, `service-access-summary.yaml`,
`rollback-summary.yaml` and `checksums.sha256`. File content remains subject
to [`redaction-rules.md`](redaction-rules.md).
