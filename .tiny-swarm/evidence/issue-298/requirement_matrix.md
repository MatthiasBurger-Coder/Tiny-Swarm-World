# RC1-R02 Requirement Matrix

Issue: [#298](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/298).
Candidate: `c921e69533450fba86d908e2990c106bef87769a`. Status: DONE; audit: PASS.

| ID | Requirement | Implementation and verification evidence | Status |
|---|---|---|---|
| R02-01 | Identify native VM, OS/architecture, systemd/kernel, filesystem, Incus network/storage and capacity. | TSW-RC1-Ubuntu, Ubuntu 26.04.1 x86_64, kernel 7.0.0-31-generic, systemd 259, ext4, Incus 6.0.5/default dir pool/incusbr0; qualification snapshots. | VERIFIED |
| R02-02 | Establish authenticated supported access with truthful failure diagnostics and no weakened SSH policy. | Successful SSH as the operator-provided account with checked known-host key; initial wrong-user rejection remains history, not a current defect. | VERIFIED |
| R02-03 | Verify ownership/isolation and explicit consent before fresh installation. | Existing full user approval; target-handover.json and dns-handover.json; empty rc1-native-20260913 project; original UUID/storage retained. | VERIFIED |
| R02-04 | Execute fresh installation, full acceptance, reconcile without reset, acceptance, update and acceptance. | Canonical full 14-operation run at c921, including recovery and four successful 25-live-test/seven-API phases. | VERIFIED |
| R02-05 | Verify manager/workers, every node Docker, Ready/Active Swarm, routes and service readiness. | Canonical platform verification, before/after eight-service readiness and current runtime snapshot; three expected provider UUIDs. | VERIFIED |
| R02-06 | Reconcile preserves identities, data and credentials without duplicate resources. | Fresh-post-reconcile/update/recovery and after-host-restart private equality comparisons; no unrelated ServiceSpec drift. | VERIFIED |
| R02-07 | Include native credential parity using the existing #277 follow-up suites. | Canonical existing Classic authenticated acceptance; each phase checks nine browser routes and seven positive/invalid-credential API assertions, zero errors/failures/skips. | VERIFIED |
| R02-08 | Execute controlled native reboot and subsequent authenticated use; share failure coverage with R03. | Actual systemctl reboot with changed boot ID; startup 100.427 seconds and 25+7 authentication 60.164 seconds; native node/rollout recovery package. | VERIFIED |
| R02-09 | Record exact SHA, true native-host provenance, commands, timing, exits and redacted evidence. | c921 full lifecycle/reboot; checksummed native JSON; kernel is native, not WSL. Manual execution is labeled native-manual. | VERIFIED |
| R02-10 | Finish on the final candidate; earlier successes remain historical after affected changes. | Full native fresh/reboot executes c921 exactly; bedb shared fault/node tests have explicit verified unchanged product scope in R01 provenance. | VERIFIED |
