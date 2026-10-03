# Issue 363: final source applicability and RC1 scenario crosswalk

Independent source-impact verdict: **PASS for the retention boundaries below**.
This is an applicability assessment, not a whole-issue completion decision.
Execution states are supplied by the execution owners and linked to the checked portable evidence package. Whole-issue completion remains the independent auditor's decision.

## Source attribution and comparisons

Historical RC1 product: `c921e69533450fba86d908e2990c106bef87769a`.
Successful fresh WSL installation: `1bd3dafd096e51f856cdf8fb0da85bdf22372421`.
Integrated quality fixes: `bdd73f58`.
Final runtime/test candidate: `89357c4a1fd463bbe5ee2ae9dac074180513eace`.
Every retained execution keeps its actual recorded SHA. Retention does not mean
that it executed the final candidate, and original failures remain failures.

The reviewer inspected actual Git diffs. `1bd3dafd..bdd73f58` changes only the
quality findings document, the registry README hash, and the legacy Pester test
helper. Runtime, configuration, build inputs, dependencies and live suites are
identical. `bdd73f58..89357c4a` changes six files: two evidence documents, two
focused test modules, the node provider and the credential-transition runner.
The only product changes mark successfully verified node creation and start as
`applied=True`. Provider commands and verification are unchanged; these flags
correct the mutation/progress evidence produced after the physical operation.
Already-running node results retain their existing no-mutation semantics.

The credential-transition helper now collects hidden fields from the same local
Jenkins login form before submitting explicit credentials. It retains the
authenticated-session precondition, source-selection assertions and restoration
checks. Its four affected live scenarios require final-source execution.

These comparisons returned no differences:

```sh
git diff --exit-code 1bd3dafd bdd73f58 -- src infra tools .github pyproject.toml setup.cfg setup.py requirements.txt requirements.lock .importlinter
git diff --exit-code bdd73f58 89357c4a -- infra tools .github src/tiny_swarm_world/application src/tiny_swarm_world/domain 'src/tiny_swarm_world/infrastructure/composition*'
git diff --exit-code bdd73f58 89357c4a -- tests/e2e/classic/run_authenticated_acceptance_live.py tests/e2e/classic/browser_e2e_contract.py tests/e2e/classic/authenticated_service_contract.py tools/live/run_classic_acceptance.py
```

Consequently, retain unaffected physical installation, update, recovery,
restart, identity, data, configuration and canonical authentication observations.
Do not retain incorrect mutation classifications as correct. Final-source node
regressions and live stopped-worker reconciliation supersede affected reporting.

## Historical scenario crosswalk

IDs and contracts below are the twelve mandatory scenarios from
`.tiny-swarm/evidence/issue-302/traceability.md`. The architectural refactor from
`c921e695` to `1bd3dafd` changed installer/CLI orchestration, platform workflows,
preflight/resource checks, deployment/secret consumers, network/process adapters,
composition, the Jenkins image and Portainer compose. Those old whole-candidate
live results are historical, not automatically valid for the new runtime.

| ID | Contract | Replacement and final-source applicability | Execution snapshot |
|---|---|---|---|
| S01 | Local quality, installer debugger and configured static preflight | Current final quality must cover changed tests, reporting producers and preflight. Historical local counts are not reused. | Final reviewed gate2377PASS/18existing skips, configured debugger/preflight and per-host canonical diagnostics are in the checked package. |
| S02 | WSL pre-live diagnostics | Current host/protected storage, canonical preflight and Windows bridge checks replace old diagnostics. Changed Windows/process and socat adapters prohibit assuming old reachability. | Current bridge preflight passes; scoped Windows CA/hostname route checks pass. Default Windows trust prerequisite remains explicitly unpassed. |
| S03 | WSL fresh installation | Retain clean `1bd3dafd` managed fresh reset/install: empty inventory, three replacement UUIDs, bootstrap/deploy/readiness. Later changes do not alter physical installation. Old created-node mutation metadata is not upgraded. | Retained executed success; no additional reset needed solely for final fixes. |
| S04 | Post-install browser/API acceptance | Retain clean `1bd3dafd` WSL baseline, 25 live tests plus seven API checks without errors/failures/skips. Canonical suite and runtime authentication unchanged. Native uses its new clean chain. | WSL retained success; native canonical chain success reported. |
| S05 | WSL reconcile and acceptance | Retain clean `1bd3dafd` healthy reconcile/no-op, stable UUIDs and post-reconcile 25+7. Healthy no-mutation branches unchanged. Final stopped-worker reporting is separately superseded. | Retained success plus final-source worker convergence, unchanged repeat and authentication pass. |
| S06 | WSL update and acceptance | Current distinct reversible image A to B, unchanged repeat, recovery plan and unrelated state continuity replace historical RC1 results. Physical `bdd73f58` observations remain applicable after reporting/test-only fixes. | Current update/recovery passes; retain exact executed source per artifact. |
| S07 | Representative missing prerequisites fail closed | Rerun existing mocked prerequisite modules and changed preflight/completeness regressions. No live destructive prerequisite fault injection is required. | Six relevant mocked prerequisite modules122PASSzero skips/failures/errors plus the final2377fullgate verified. |
| S08 | Controlled partial-state recovery | Current failed rollout, original-direction recovery, repeat and owned worker recovery on both hosts. False no-op after actual worker start is historical defect evidence; final `89357c4a` must report convergence, then no-op on unchanged repeat, with full authentication. | WSL and native final-source affected worker reruns pass; both controlled-fault/recovery scenarios pass. Failed attempts remain separate. |
| S09 | Selected restart and authenticated recovery | Actual selected WSL distribution restart and native host reboot, stable provider/Swarm identities, persistent fixtures, bounded readiness and 25+7 acceptance. Service-only restart is insufficient. Physical `bdd` restart evidence remains applicable if already executed successfully. | Native second actual host reboot passed with representative Jenkins application content preserved, readiness within162.761047seconds and25+7. Actual isolated WSL restart also passed with Jenkins application content preserved, readiness within127.202seconds and25+7. Primary Ubuntu restoration also passed readiness within116.957seconds,25+7 and original application contents/identities; final Windows routes passed. |
| S10 | Native fresh installation | New clean canonical native chain replaces old RAM-gated/dirty formal partial results. Retain physical clean `bdd` fresh install after final reporting/test-only fixes; retain actual source. | Current canonical 14-operation chain passes; original existing-target Infisical failure remains failed. |
| S11 | Native reconcile and acceptance | Successful separate reconcile after fresh current install, without reset, followed by identity/configuration/data/credential comparison and 25+7. Fresh install alone is insufficient. | Included in successful canonical native chain; final-source worker convergence, unchanged no_op repeat and25+7 also pass. |
| S12 | Native update and acceptance | Distinct image A to B, repeated no-op, continuity and acceptance; controlled fault and original recovery remain distinct observations. | Canonical native chain and supplemental fault/recovery/worker evidence pass. |

Every replacement bundle must preserve scenario/host/profile, exact revision,
configuration provenance, command, timestamps/duration, exit, LIVE classification,
readiness before/after, bounded retries/remediation, rollback/cleanup,
value-free persistent comparison results, checksums and independent review.

## Credentials, lifecycle and evidence boundaries

The domain/application credential resolver and precedence contract remain
unchanged, allowing historical evidence of selection-policy semantics to be
retained explicitly as historical. The earlier RC1 unchanged-consumer proof no
longer holds after changes to secret manifest loading, stack snapshots,
composition and Infisical adapters. Thus the existing Vault-only and distinct
operator/Vault-conflict transition runner is required on both hosts, four actual
final-source scenarios, with verified restoration. The hidden-form fix further
requires these scenarios at `89357c4a`. WSL both scenarios pass with failed
attempts retained; both native scenarios also pass LIVE_VERIFIED with restorationcomplete=true; native actual reboot and application-data continuity also pass; isolated actual WSL restart acceptance also passes; primary restoration and final Windows routes also pass; independent whole-issue review remains the final authority.

Issue 363 also names status and destroy/cleanup. There is no supported
`platform status` action, historically or currently: status uses documented
`platform verify` structured status/readiness plus runtime inventory. Do not
invent a new command or treat expected unsupported exit 2 as a missing feature.
Scoped managed reset demonstrates cleanup but does not by itself establish the
distinct supported destroy command; final evidence must distinguish them.

A failed existing-target Infisical setup followed by repair/reset and fresh
installation must retain the failure. Fresh installation does not prove in-place
recovery of that failed target. Diagnose preexisting inconsistent configuration
versus an actual supported bootstrap regression; reset must not conceal the
latter. A separate successful fresh-target reconcile/authentication is necessary.

WSL restart requires changed distribution PID1/PID namespace, with unchanged
shared kernel boot ID. Native reboot requires a changed host boot ID. The planned
quiesced WSL procedure is documented in
`documentation/evidence/rc1-wsl-planned-restart-20260913.md`. Hard power loss or a
new Windows browser suite is not added to issue 363. Scoped Windows CA checks
do not prove default Windows trust, and WSL Firefox does not independently prove
Windows host reachability.

## External RC1 evidence

Historical #300 CI/Sonar successes remain exact-candidate records; changed
source/tests and expanded Python 3.12/3.13/3.14 inputs prevent calling them
current-candidate analyses. Changed Dockerfile inputs likewise invalidate old
container scan input hashes. The #301 hosted workflow is unchanged but its
canonical runner changed: manual current host chains replace behavioral
scenarios, not the historical fact of GitHub-hosted execution.

Issue 363 behavioral completion does not itself request a new RC1 release
qualification or require republishing all historical external checks. Preserve
the existing RC1 decision for its recorded candidate; state present external
availability/results separately. This document cannot establish whole-issue
DONE while scenario results or final independent acceptance remain pending.
