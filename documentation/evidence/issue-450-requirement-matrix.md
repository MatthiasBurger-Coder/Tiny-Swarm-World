# Issue #450 requirement matrix

Baseline: `e9b9fe51` (main), 2026-10-28. Status: IN PROGRESS.
Live operations are not authorized by the issue. Local verification and live
qualification are distinct.

| ID | Requirement | Implementation and verification | Status |
| --- | --- | --- | --- |
| W10-01 / AC1 | Align README, user guide, CLI help and troubleshooting with actual commands and tested behavior. | README, usage and troubleshooting corrected; help inspected and CLI regression suites run on SSH/WSL. Complete example coverage remains open. | OPEN |
| W10-02 / AC2 | Document fresh selective setup, dependency additions, adding services, product and component upgrades with supported examples. | README and usage link existing detailed guides; WSL Jenkins/SonarQube preview shows foundations and Nexus. Remaining examples require verification. | OPEN |
| W10-03 / AC3 | Explain Portainer backup and API-independent recovery, image rollback versus data restoration and migration limits. | Troubleshooting and existing component guide; independent verification pending. | OPEN |
| W10-04 / AC4 | Audit LCM-01–05 against architecture, tests, live evidence, exact scope and limits; distinguish mock from live results. | Parent audit references W09 qualification and P01–P15 crosswalk; full independent audit pending. | OPEN |
| W10-05 / AC5 | Reconcile each parent checklist item only from verified evidence. | Local parent audit retains all entries open pending complete evidence; GitHub checklist unchanged. | OPEN |
| W10-06 | Use Mermaid where useful; document Incus and Portainer foundations and dependency reasons. | Usage overview diagram and selection guide; rendering unverified. | OPEN |
| W10-07 | Check help, invalid inputs, previews, no-op, failures and consent; run applicable QUALITY gates. | SSH/WSL: 54 CLI/documentation tests and full quality gate (3,224 tests, 36 skipped) passed; help and selection preview inspected. Remaining example coverage requires review. No infrastructure mutations. | OPEN |
| W10-08 | Preserve evidence provenance, exact source and host attribution and no unverified live claims. | Existing W09 records and explicit limitations. | OPEN |
| W10-09 | Independent completion audit and required issue evidence package. | Issue-completion discipline and `.tiny-swarm/evidence/issue-450/`. | OPEN |

W01–W08 are closed as completed; W09 is closed as not planned and its
qualification report remains INCOMPLETE. Closure of the issue is not live proof.
