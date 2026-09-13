# RC1-R08 Requirement Matrix

Issue: [#309](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/309).
Candidate: `c921e69533450fba86d908e2990c106bef87769a`. Status: DONE; audit: PASS.

| ID | Requirement | Implementation and verification evidence | Status |
|---|---|---|---|
| R08-01 | Inventory services/images/dependencies/admin routes/sockets/networks at candidate SHA. | 40 observed task records across two hosts; service-access route inventory; requirements.lock and R04 SBOM. | VERIFIED |
| R08-02 | Execute existing dependency/SBOM/container-configuration checks with versions, revisions and dates. | R04 exact input-equivalent fresh checks: pip-audit 2.10.1, CycloneDX 1.4, Trivy 0.74.0; 13 packages; three Dockerfiles, 60 successful checks, zero HIGH/CRITICAL configuration findings. | VERIFIED |
| R08-03 | Classify applicable findings and reviewed residuals with severity, impact, owner and review condition. | risk-dispositions.md; previous DS-0002 remediation rescanned; actual fresh non-root task users and complete startup verified. | VERIFIED |
| R08-04 | Verify socket/admin/direct/routed/network boundaries without platform redesign. | Eight bounded live checks per host plus full canonical authenticated route/API acceptance; explicit socket capability residual. | VERIFIED |
| R08-05 | Record exact tested image identities and retained-tag limitations. | Each of 20 running task images per host has immutable image ID and resolved repository digest; host builds differ explicitly. | VERIFIED |
| R08-06 | Confirm internal-test credential/exposure boundary and supported overrides. | Existing credential catalog/override ADR and protected-input guide; positive/invalid-credential API checks; no new password/SSO requirements. | VERIFIED |
| R08-07 | Document reproducible procedure, evidence and pass/block rules using existing tools. | Updated documentation/security/rc1-classic-security-evidence.md and candidate artifacts; no new scanner CI. | VERIFIED |
| R08-08 | Supply reports and dispositions to R06; unresolved applicable blockers prevent acceptance. | Complete candidate package and explicit dispositions available for final R06 row audit; no applicable unresolved blocker found in declared check scope. | VERIFIED |
