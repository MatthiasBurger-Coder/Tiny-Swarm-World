# RC1-R02 Test Results

| Actual evidence | Result |
|---|---|
| Fresh run 20260912T235814.253797Z, exact c921 | LIVE_VERIFIED; all 14 operations exit zero |
| Setup | 1476.238 seconds; all 18 configured phases complete |
| Platform verification / initial eight-service readiness | PASS, 2.680 / 1.406 seconds |
| Baseline authentication | 25 live tests + seven API checks, 62.623 seconds |
| Reconcile | PASS, 1.116 seconds, preserved configuration/identity/fixture |
| Post-reconcile authentication | 25+7 PASS, 59.443 seconds |
| Update / post-update authentication | 12.368 / 58.393 seconds, PASS |
| Recovery / post-recovery authentication | 12.405 / 59.897 seconds, PASS |
| Controlled native systemd reboot | Exit zero; boot ID changed; SSH recovered after 38.279 seconds |
| Startup readiness after reboot | 100.427 seconds from verifier start, under 600-second bound |
| Post-reboot authentication | 25+7 PASS, 60.164 seconds; no post-start repair |
| Shared native worker failure | Same provider identities; recovery 3.036 seconds; full authentication passes |
| Shared native failing image | Expected rollout_failed; canonical recovery and repeated no-op recovery pass |

Each 25-test phase means eight readiness tests before, nine browser tests and
eight afterward. All successful phases have zero errors/failures/skips. Manual
native execution is not a GitHub-hosted run. Complete authenticated JSON and
phase timing fields are retained in the checksummed native-fresh directory.

Observed capacity: 8 CPU threads, MemTotal
24078420 KiB, ext4 and 210991529984 free bytes at
the pre-reboot observation. These are host snapshots, not peak measurements or
universal minimum guarantees. Incus uses the retained default dir pool and shared
incusbr0, with three distinct fresh provider UUIDs.

Full product-equivalent candidate quality already passed: 2066 tests, 18 explicit
live/optional skips, 674 typechecked files, three import contracts and 18 architecture
tests. This publication changes only evidence and runs diff/policy, artifact JSON,
hash, redaction and link checks. It omits a duplicate full runtime suite under
QUALITY.md; PR-specific quality/compatibility/Sonar are observed before merge.
