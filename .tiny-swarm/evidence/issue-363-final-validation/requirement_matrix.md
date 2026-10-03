# ARCH-03.20 requirement matrix

Issue: #363, parent #313. Final runtime/test candidate `89357c4a1fd463bbe5ee2ae9dac074180513eace`, branch `fix/issue-363-final-validation`. Status: DONE. Independent whole-issue completion audit: PASS; open requirements: none.

This matrix preserves original R363 identifiers. Earlier incomplete audit/results remain in `.tiny-swarm/evidence/issue-363/`; this campaign supersedes status only through executed evidence and reviewed applicability. The preimplementation campaign scope was recorded before the MUT/COOKIE corrections.

| ID | Requirement | Implementation / verification evidence | Status |
|---|---|---|---|
| R363-01 | Preserve supported behavior through real lifecycle scenarios. | WSL lifecycle qualified; native canonical chain qualified; actual native host and selected WSL distribution restarts passed; Primary Ubuntu restoration and final25+7/actual-data continuity passed. | VERIFIED |
| R363-02 | Validate install and bootstrap. | WSL clean1bd3 fresh install; native cleanbdd fresh install after observed empty inventory; new identities and formal post-install25+7. Reviewed unchanged runtime applicability to893. | VERIFIED |
| R363-03 | Validate deploy and supported status. | Canonical setup/platform verify and authenticated acceptance on both hosts. platform status is unsupported historically and currently; its exit2 remains guard evidence. | VERIFIED |
| R363-04 | Validate reconcile and restart. | WSL healthy reconcile/service replacement/managed cold restart passed; native canonical reconcile passed. Actual selected distribution/native host reboot passed; Primary Ubuntu restoration and final25+7/actual-data continuity passed. | VERIFIED |
| R363-05 | Validate supported update. | Both hosts use a genuinely distinct correctly attributed packaging image; preview/apply and25+7 passed; unchanged repeat no_op. | VERIFIED |
| R363-06 | Validate recovery and destroy/cleanup. | Both hosts real exit73 failed rollout and canonical recovery+25+7 passed. Scoped fresh-install reset/destroy observed empty managed inventory. Primary Ubuntu restoration and final25+7/actual-data continuity passed. | VERIFIED |
| R363-07 | Relevant unit/integration/E2E/live tests pass. | Final code-equivalent full quality2377PASS18existing skips; both-host canonical25+7 suites pass. Both actual restart acceptances passed; Primary Ubuntu restoration and final25+7/actual-data continuity passed. | VERIFIED |
| R363-08 | Classic Docker Swarm profile stays operational. | Both hosts full Classic service/readiness/authentication proved; both actual restart acceptances passed; Primary Ubuntu restoration and final25+7/actual-data continuity passed. | VERIFIED |
| R363-09 | WSL2 supported flows stay operational. | Fresh/reconcile/update/recover/worker/service restart/credential transitions pass; actual isolated distribution restart passed with real application-content continuity; Primary Ubuntu restoration and final25+7/actual-data continuity passed. | VERIFIED |
| R363-10 | Native Linux supported flows stay operational. | Fresh/canonical14/update/recover pass; affected worker and both credential cases passed on893; two actual host reboots verified. Second seeded-content reboot: changed boot ID, readiness within162.761047seconds≤600,25+7 and actual Jenkins application-content continuity passed. First boot retains its narrower identity/configuration/authentication scope. | VERIFIED |
| R363-11 | Secret bootstrap stays compatible. | Both-host install/bootstrap/authentication pass; final893WSL Vault-only and operator/Vault conflict pass with verified restore; both native transitions also pass LIVE_VERIFIED with restorationcomplete=true. | VERIFIED |
| R363-12 | CLI contracts stay compatible. | Canonical14 chain and local CLI regression checks; mutation-reporting fix retains commands and corrects applied evidence. Final native worker convergence/no_op+authentication passed. | VERIFIED |
| R363-13 | Replace refactor-invalidated RC1/live evidence. | S01–S12 crosswalk and reviewed source-retention assessment; all actual scenarios passed; primary restoration passed. | VERIFIED |
| R363-14 | Report failure and non-success states truthfully. | Protected phase ledgers retain original failures, unsupported actions and retries with separate source/run identities. No old CI/Sonar success relabeled current. | VERIFIED |
| R363-15 | Preserve WSL preflight at existing operator memory setting. | Original20GB WSL configuration preserved; supported WSL16GiB/native15GiB floors in1bd3+ unchanged by finalfixes. Native18.73GiB qualified with explicit8/6/3GiB node override. | VERIFIED |

| Additional ID | Requirement | Verification | Status |
|---|---|---|---|
| R363-MUT-01 | Verified actual node creation/start exposes applied=true; unchanged running nodes remain no_op. | Real-producer regression RED6fail→98focusedPASS; fullgatePASS; final893WSL real stopped-worker converged/executedtrue then repeated no_op/executedfalse+25+7. Final893native real stopped-worker convergence then repeatno_op,25+7 and stable identities/specs also passed. | VERIFIED |
| R363-COOKIE-01 | Actual Jenkins login form hidden fields are submitted in the same session with explicit credentials. | RED3fail→6PASS; unchangedCSRF/session invalidation/TLS/restore enforcement; final893WSL both transitions PASS. Both final893native Vault-only and conflicting-source cases also passed, restorationcomplete=true. | VERIFIED |

## Execution and applicability

Explicit user live consent covers disposable native host, managed reinstall, lifecycle/fault/recovery and parallel agents. Root integrates code/evidence; target owners serialize shared mutations. WSL distribution restart uses separately owned `TSW-RC1-Isolated` after primary Ubuntu quiescence, preserving unrelated Docker and the active Codex environment.

Installation scope is fresh managed state, not a factory-clean OS. S01–S12 mapping is in `rc1_applicability.md`; source attribution is retained in `runtime-equivalence.md` and final independent applicability assessment. Older created/started false-no_op classifications are not upgraded. All four CRED09 cases require final893. External hostedCI/Sonar and a newRC1 release declaration are outside this local behavioral completion campaign.

## Evidence crosswalk

- R36301–06/08–10/12: test_results.md; portable/wsl-fresh.json; portable/linux/summary.json and phase-ledger.json; portable/wsl-isolated/summary.json and phase-ledger.json; portable/wsl-primary/portable-aggregate.json and phase-ledger.json.
- R36307: local-verification.json, complete protected full-gate log checksum, and per-host live test counts.
- R36311/COOKIE01: both-host final893 credential transition records in phase ledgers plus verified restoration and focused regression evidence.
- R36313: rc1_applicability.md and independent final source-applicability assessment.
- R36314: per-host failed-invocation ledgers, remaining_risks.md and actual executed source attribution.
- R36315: native effective resource provenance and current host-specific preflight evidence.
- MUT01: committed provider regression, per-host final-source real worker convergence/unchanged-repeat records.
