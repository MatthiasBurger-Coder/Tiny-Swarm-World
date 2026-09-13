# RC1-R03 Scenario Matrix

- R03-01: Define fresh, every post-phase, fail-closed, partial recovery and restart scenarios. Evidence: scenario_matrix.md; canonical 14-operation runner; first failed and corrected restart records.
- R03-02: Qualify source, protected native runtime/evidence, consent and redaction. Evidence: Hosted R05 protected storage; 116 mocked source/storage/prerequisite tests; actual ext4 WSL host snapshots. /mnt source support is fixture evidence, not the native-path live checkout.
- R03-03: Execute Fresh → acceptance → Reconcile → acceptance → Update → acceptance without duplicate resources. Evidence: Hosted 34725969899 on exact candidate-equivalent 8eb; issue-297 continuity and unchanged provider UUIDs.
- R03-04: Exercise controlled partial deployment and managed service/node recovery without losing healthy state. Evidence: Typed rollout_failed and canonical recovery in issue-297; WSL worker stop/reconcile/full auth; observed Pulsar endpoint failure and targeted recovery retained.
- R03-05: Selected WSL restart restores identities, Docker/Swarm/routes and application readiness in bounded time. Evidence: Cycle2 planned Docker-quiesced distribution restart: 133.629 seconds startup verification, changed PID identity, unchanged kernel boot ID/provider UUIDs.
- R03-06: Run authenticated service operations after restart. Evidence: Cycle2 complete 25 live tests and seven API checks; 87.931 seconds, zero errors/failures/skips.
- R03-07: Retain exact SHA, profile/host, commands, timing, exits and protected redacted results. Evidence: Checksummed WSL/native packages and provenance; secret/configuration comparisons expose equality only.
- R03-08: Retain failed attempts and rerun affected/dependent scenarios after fixes. Evidence: First boot LIVE_PARTIAL; targeted repair followed by full authentication; separate planned cycle2 passes without post-start repair.
- R03-09: Cover missing Incus, storage/network, artifact/configuration and secret-protection prerequisites safely. Evidence: prerequisite-fixtures.json maps exact cases; 116 tests pass, zero skips. These are local fixtures, not live fault injection.
- R03-10: Apply shared failure/recovery checks on native Linux where host semantics differ. Evidence: Native bedb product-equivalent rollout/node recovery; c921 actual VM reboot, changed boot ID and full 25+7 authenticated acceptance.

The first failed WSL restart remains LIVE_PARTIAL; only the separate planned
cycle2 is LIVE_VERIFIED. Local fixtures and actual live scenarios are distinct.
