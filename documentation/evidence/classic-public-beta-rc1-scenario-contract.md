# Classic Public Beta RC1 Scenario Contract

Issue #252 uses deterministic tests for lifecycle policy and separate
host-specific evidence for live observations. The local tests may use only
synthetic resources, temporary paths and redacted summaries; they must not
start Incus, Docker, Swarm, compose, browser or service operations.

Each host/scenario evidence bundle records at least:

- scenario identifier;
- host and target label;
- commit and start/end timestamps;
- lifecycle state and result classification;
- exit status;
- readiness and transition summary;
- bounded retry metadata and remediation;
- rollback/cleanup result;
- redacted evidence-file references;
- defect summary, checksum and independent reviewer.

The only permitted final decision values are:

- `RC1_ACCEPTED`;
- `RC1_REJECTED_BLOCKERS`;
- `RC1_REJECTED_EVIDENCE_INCOMPLETE`.

`RC1_ACCEPTED` requires at least one required scenario and a complete bundle
with `LIVE_VERIFIED`, exit code zero, `redacted` evidence and `passed` for
every required scenario. `refused`, `blocked`,
`resource-gated`, `failed-to-apply`, `failed-to-prepare`, `failed-to-verify`,
`partial`, `degraded`, missing evidence or failed verification remain
non-success states and cannot be converted into acceptance.

Reconcile evidence must compare stable resource identities, duplicate counts,
unrelated healthy state and readiness before and after the run. Update evidence
must prove preservation of unrelated healthy state. Restart evidence must prove
the same identities return to a ready state. Raw passwords, tokens, command
output, environment files and sensitive headers are never evidence.
