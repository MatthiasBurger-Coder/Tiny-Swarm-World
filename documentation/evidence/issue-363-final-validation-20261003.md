# ARCH-03.20 final behavioral compatibility validation

Issue: [#363](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/363). Runtime/test candidate: `89357c4a1fd463bbe5ee2ae9dac074180513eace`. Integration branch: `fix/issue-363-final-validation`. **Completion: DONE. Independent full-issue audit: PASS; open requirements: none.**

## Integrated corrections

The requested registry fingerprint and native WSL/UNC Pester fixes are integrated. Live testing also exposed an existing node mutation-reporting omission and a missing Jenkins login-form token in the credential test helper. Verified node creation/start now reports the actual mutation; cookie login submits hidden fields through the same session. Commands, CSRF enforcement, TLS, credential selection and restoration checks remain intact.

The final tested code passed the full local quality gate: **2,377 tests, 18 existing skips**, 37 architecture tests, six import contracts and typechecking of 732 source files. Independent commit review confirmed identical bytes between the tested tree and committed candidate. Final documentation edits use whitespace, JSON, checksum and traceability checks; Python source/tests are unchanged.

## Lifecycle results

| Scope | Verified result |
|---|---|
| Fresh managed installation, bootstrap and deployment | Both hosts passed from observed empty managed inventory, with three new node identities and immediate authenticated acceptance. WSL executed clean `1bd3dafd`; native executed clean `bdd73f58`. Independent source review retains physical applicability without changing executed revisions. |
| Status and reconciliation | Both hosts passed supported `platform verify` and stable-identity reconciliation. Final-source worker loss produces `converged` and executed mutation, followed by unchanged `no_op`. |
| Update | Both hosts passed a genuine distinct packaging-image update, preview/application, authenticated acceptance and unchanged repeat. This is image compatibility, not a Jenkins binary-version upgrade claim. |
| Failure/recovery and cleanup | Real exit-73 rollout failure was classified `rollout_failed`; canonical recovery and authenticated acceptance passed. Scoped reset/destroy observed empty owned inventory. |
| Secret compatibility | Vault-only and conflicting operator/Vault source transitions passed on both hosts at final `89357c4a`, with session invalidation, reapplication, consumer restart and complete verified restoration. |
| Actual native host reboot | Two reboots passed. The second preserved a real Jenkins job, successful build and archived content; readiness returned within **162.761 seconds**, then 25 live tests plus seven API checks passed without errors or skips. |
| Actual selected WSL distribution restart | Isolated distribution PID1/PID namespace changed; shared kernel and primary Ubuntu were preserved. Real Jenkins contents survived. Readiness returned within **127.202 seconds** (conservative observation: 128.564), then 25+7 passed without errors or skips. |
| Final primary Ubuntu restoration | Original nodes, application contents, configuration, credentials and cluster identities restored. Readiness passed within **116.957 seconds**, then 25+7 passed. All 18 continuous services reached desired replicas; bootstrap completed successfully. |

The native canonical 14-operation chain also passed every operation, including four complete 25+7 authenticated suites and four 8/8 readiness suites. Both primary targets finish healthy; the isolated distribution returned to its prior stopped/disabled state with retained data. Unrelated Ubuntu Docker resources and listeners were preserved.

## Provenance and limits

Fresh installation means reset of owned managed state, not a factory-clean operating system. The native host has 18.73 GiB and uses an explicit external 8/6/3 GiB node fixture; repository 10/8/1 GiB defaults remain unchanged. This does not qualify a physical 15 GiB host or sustained heavy workload. Original custom operator input and database backup remain privately preserved.

The initial native Infisical sync failure came from missing non-secret external reference names. Canonically prepared operator inputs retained original credentials and passed setup/verification/authentication before the separate fresh reset. The fresh target's catalog credential fixture is separately attributed.

Nine Windows HTTPS routes passed again after Ubuntu restoration using the actual current public CA and hostname checks. Default Windows private-CA trust still fails; no trust store was changed. Revocation availability remains `NOT_VERIFIED`. The scoped client check used curl's documented [revocation best-effort option](https://curl.se/docs/manpage.html#--ssl-revoke-best-effort) for missing/offline revocation endpoints. No Windows browser suite or global trust installation is claimed.

Original unexpected observation, login, deployment, helper and early readiness failures remain failed invocations; successful bounded retries are separate evidence. Both restart deadlines remained 600 seconds. Missing supplemental native operation timings and slight isolated clock differences are explicit; no timestamps or causes were invented. The original unsupported `platform status` exit 2 remains guard evidence; supported status uses `platform verify`.

## Traceability and completion authority

The [independent source-applicability assessment](issue-363-final-source-applicability-20261003.md) maps all twelve historical RC1 behavioral scenarios to successful replacements or reviewed retention. Earlier physical results keep their actual SHA; affected mutation and credential cases use final source. Historical hosted CI, Sonar and RC1 decisions are not relabeled as current results, and this campaign does not declare a new RC1 release.

The requirement matrix, six required evidence files, portable per-host summaries/ledgers/checksums and independent audit are in `.tiny-swarm/evidence/issue-363-final-validation/`. Historical incomplete evidence remains intact with a pointer to this campaign. The final independent `completion_audit.md` determines whole-issue completion. No remote publication or GitHub state change was requested.

The independent completion auditor confirmed all three perspectives: Requirement Lead, System Architect and Test/Evidence Reviewer. Final documentation/evidence integration does not change the qualified runtime/test/configuration bytes; executions retain their recorded source revisions. The administrative GitHub issue state was not changed.
