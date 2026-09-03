# Requirement Matrix: #284 / CRED-06

The matrix was captured on the issue branch before final review and verification
of the issue-specific documentation/UX edits. CRED-04 already supplied the
catalog and override implementation baseline used by this slice.

| ID | Requirement | Implementation/documentation target | Verification | Status |
|---|---|---|---|---|
| CRED-06-REQ-001 | Getting-started path is `clone -> install -> login` without credential-preparation ceremony. | README quick-start and installation guide | link/reference review; docs diff | VERIFIED |
| CRED-06-REQ-002 | Installer output gives actionable service URLs and login identifiers. | `simple_installer._print_operator_credentials` | installer output regression test | VERIFIED |
| CRED-06-REQ-003 | Canonical internal-test login convention has one authoritative location. | CRED-01 catalog linked by README, handbook, installation guide, output | catalog/reference search | VERIFIED |
| CRED-06-REQ-004 | Component-specific exceptions remain discoverable and catalog-derived. | catalog link and SonarQube exception reference | documentation review | VERIFIED |
| CRED-06-REQ-005 | Override precedence and Infisical role are accurate. | CRED-03 contract links and operator guidance | contract/reference review | VERIFIED |
| CRED-06-REQ-006 | Enterprise identity and reachability boundary is explicit. | user handbook and operator configuration contract | documentation search | VERIFIED |
| CRED-06-REQ-007 | Deleted generated/recovery mode documentation is absent or clearly negative. | `.env.example`, installation, RC1 bootstrap, console output docs | stale-reference search | VERIFIED |
| CRED-06-REQ-008 | `.env.example` does not imply manual values are required for ordinary internal-test install. | commented optional override template | template inspection and installer tests | VERIFIED |
| CRED-06-REQ-009 | Console UX does not print raw credential values. | safe target/convention output | output redaction regression tests | VERIFIED |
| CRED-06-REQ-010 | Documentation-only/product-UX changes pass quality gates. | repository verification | quality gate and focused tests | VERIFIED |
| CRED-06-REQ-011 | Changed product behavior meets coverage threshold. | output branch and tests | branch-aware diff coverage | VERIFIED |
