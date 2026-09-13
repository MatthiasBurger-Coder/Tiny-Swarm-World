# RC1-R03 Requirement Matrix

Issue: [#299](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/299).
Candidate: `c921e69533450fba86d908e2990c106bef87769a`. Status: DONE; audit: PASS.

| ID | Requirement | Implementation and verification evidence | Status |
|---|---|---|---|
| R03-01 | Define fresh, every post-phase, fail-closed, partial recovery and restart scenarios. | scenario_matrix.md; canonical 14-operation runner; first failed and corrected restart records. | VERIFIED |
| R03-02 | Qualify source, protected native runtime/evidence, consent and redaction. | Hosted R05 protected storage; 116 mocked source/storage/prerequisite tests; actual ext4 WSL host snapshots. /mnt source support is fixture evidence, not the native-path live checkout. | VERIFIED |
| R03-03 | Execute Fresh → acceptance → Reconcile → acceptance → Update → acceptance without duplicate resources. | Hosted 34725969899 on exact candidate-equivalent 8eb; issue-297 continuity and unchanged provider UUIDs. | VERIFIED |
| R03-04 | Exercise controlled partial deployment and managed service/node recovery without losing healthy state. | Typed rollout_failed and canonical recovery in issue-297; WSL worker stop/reconcile/full auth; observed Pulsar endpoint failure and targeted recovery retained. | VERIFIED |
| R03-05 | Selected WSL restart restores identities, Docker/Swarm/routes and application readiness in bounded time. | Cycle2 planned Docker-quiesced distribution restart: 133.629 seconds startup verification, changed PID identity, unchanged kernel boot ID/provider UUIDs. | VERIFIED |
| R03-06 | Run authenticated service operations after restart. | Cycle2 complete 25 live tests and seven API checks; 87.931 seconds, zero errors/failures/skips. | VERIFIED |
| R03-07 | Retain exact SHA, profile/host, commands, timing, exits and protected redacted results. | Checksummed WSL/native packages and provenance; secret/configuration comparisons expose equality only. | VERIFIED |
| R03-08 | Retain failed attempts and rerun affected/dependent scenarios after fixes. | First boot LIVE_PARTIAL; targeted repair followed by full authentication; separate planned cycle2 passes without post-start repair. | VERIFIED |
| R03-09 | Cover missing Incus, storage/network, artifact/configuration and secret-protection prerequisites safely. | prerequisite-fixtures.json maps exact cases; 116 tests pass, zero skips. These are local fixtures, not live fault injection. | VERIFIED |
| R03-10 | Apply shared failure/recovery checks on native Linux where host semantics differ. | Native bedb product-equivalent rollout/node recovery; c921 actual VM reboot, changed boot ID and full 25+7 authenticated acceptance. | VERIFIED |
