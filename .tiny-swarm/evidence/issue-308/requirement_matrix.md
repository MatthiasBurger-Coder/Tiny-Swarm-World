# RC1-R07 Requirement Matrix

Issue: [#308](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/308).
Candidate product: c921e695. Status: DONE; audit: PASS.

| ID | Requirement | Implementation and verification evidence | Status |
|---|---|---|---|
| R07-01 | Recheck and integrate PR307 handbook consolidation without lost topics/duplicate handbook/broken links. | PR307 merged as 3998dde7930da9ad1736f2c4c6337e5d4e04d0f5; current manual navigation and installation/usage/arc42/system render and links reviewed. | VERIFIED |
| R07-02 | Reconcile README, guides, manual, arc42 risks and audit register with current code/evidence. | Current Infisical/test-catalog behavior and explicit update semantics retained; Vaultwarden subsection clearly historical; MIN-05 corrected from actual Apache-2.0 LICENSE with dated review. | VERIFIED |
| R07-03 | Document prerequisites through first login, including static versus actual readiness. | Existing installation guide covers Python3.12/locked dependencies, Incus initialization/capacity/protected paths and WSL bridge/DNS/TLS; operator manual adds observed shared-DNS/same-distro prerequisites. | VERIFIED |
| R07-04 | Align reset, verify, reconcile, setup, supported update and recovery semantics. | README/usage/installation command review against CLI and ADR; direct setup on empty target explicitly distinguished from resetting install.sh wrapper. | VERIFIED |
| R07-05 | Execute documented journey on qualified declared-clean targets and repair missing steps. | journey-c921e695.json; actual WSL 34725969899 and native 20260912T235814.253797Z reuse host runs; initial prerequisite failures/corrections retained. | VERIFIED |
| R07-06 | Record actual install durations and available resource observations by profile. | WSL setup 1723.846 seconds; native 1476.238 seconds; real CPU/memory/disk snapshots and profile thresholds, no invented peaks or universal timing guarantees. | VERIFIED |
| R07-07 | Render/check guides, aggregates and local links without new warnings; verify commands. | Four guide/aggregate renders with pinned Linux image and failure-level WARN pass; manual local targets/explicit anchors checked; earlier wrong operator path retained. | VERIFIED |
| R07-08 | Operator-oriented completion review feeds exact evidence and limitations to R06. | completion_audit.md explicitly records root-AGENTS three-perspective fallback after real-agent limits; no new independent human/agent approval claimed. | VERIFIED |
| R07-09 | Document actual isolated-install prerequisites without changing provider behavior. | Shared Incus DNS names remain owned even when stopped; dedicated WSL bridge and PATH qualified before retry; operator-manual changes match actual failure/correction records. | VERIFIED |
