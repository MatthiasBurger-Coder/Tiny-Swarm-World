# Issue #128 Remaining Risks

| Risk | State | Next owner/action |
| --- | --- | --- |
| Actual GitHub branch-protection settings are not observed | Unknown / target documented | Authorized settings-verification workflow must record the actual rule set. |
| Required-check names and hosted status are not observed | Unknown / merge-blocking | Verify through PR checks before any protected merge. |
| SonarCloud token/result availability is external | Unknown | Treat missing/unverifiable result as non-pass when configured as required. |
| Signed commits and linear history are not repository-wide enforced | Recommended | Make an explicit adoption decision with signer/history prerequisites. |
| Dependency, SBOM and image-scan enforcement remains target/release-scoped | Evidence pending | Carry #127 policy evidence into release baseline and CAPA when findings occur. |

These are governance-state risks, not runtime or live-infrastructure findings.
They are not accepted by documenting them.
