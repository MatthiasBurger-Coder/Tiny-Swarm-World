# RC1-R06 requirement matrix

Issue #302. FULL_PATH, isolated final audit branch. Complete issue #252 body and
mandatory CI addendum are extracted in the source inventory, not reduced to nine
work packages. Historical #277 original requirements remain in its audited 25-row
matrix; current GitHub deletion does not remove them.

| ID | Requirement | Implementation / verification evidence | State |
|---|---|---|---|
| R06-01 | Extract every mandatory #252 body and CI-addendum requirement, including service/test inventories and scenario assertions. | source-requirement-inventory.json; traceability.md; inventory-and-ci-contract.md | VERIFIED |
| R06-02 | Preserve historical issue states, closure reasons, useful evidence and rerun boundaries. | history-and-applicability.md; source-issue-252.json | VERIFIED |
| R06-03 | Reconcile #285/#293 and #277 against actual credential results without deleting history. | history-and-applicability.md; credential-applicability.json; issue-296 wrapper; dated parent appendices | VERIFIED |
| R06-04 | Identify final integrated candidate and actual executed/analyzed SHAs. | candidate-provenance.json; final-ci.json; release candidate matrix | VERIFIED |
| R06-05 | Verify both-host fresh/reconcile/update/post-phase authentication, recovery/restart, credential source/drift and redaction. | issue-297/298/299/301/295/296 packages; inventory-and-ci-contract.md | VERIFIED |
| R06-06 | Verify final Quality, both supported Conda jobs, actual Sonar gate and protected hosted lifecycle. | final-ci.json; issue-300/301 packages; failure-semantics.json | VERIFIED |
| R06-07 | Rerun affected mandatory scenarios and justify every reused result. | candidate-provenance.json; credential-applicability.json; history-and-applicability.md | VERIFIED |
| R06-08 | Check every evidence row through requirement, architecture and test/evidence review. | completion_audit.md; traceability.md; explicit role fallback and retained actual independent reviews | VERIFIED |
| R06-09 | Publish exactly one supported RC1 decision from verified requirements. | documentation/release/rc1-decision.md | VERIFIED |
| R06-10 | Align EPIC/checklists, release notes, limitations and completed workflow; no tag publication. | release notes/checklist; workflow index; #294/#302 final integration record | VERIFIED |
