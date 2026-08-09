# Issue #163 Review — Sonar IP Literals

Decision: `KEEP_OPEN`

Review baseline: `main` at `ecdc71d94a72530905ecb0a41d2845921ad6debb`.
The current issue body and its three historical finding keys were re-read from
GitHub. Older duplicate issues #159 and #160 remain closed and are not reopened
or reimplemented.

## Finding trace

| Original finding | Current source evidence | Status |
|---|---|---|
| #159 / `AZ7kcUaJ8N9AxeIuoSBg` / `192.168.1.10` | `tests/domain/network/test_port_forwarding_plan.py:165` | Raw literal remains |
| #160 / `AZ7kcUaJ8N9AxeIuoSBh` / `10.0.0.5` | `tests/domain/network/test_port_forwarding_plan.py:166` | Raw literal remains |
| #163 / `AZ7kcUaJ8N9AxeIuoSBk` / `192.168.1.10` | `tests/domain/network/test_port_forwarding_plan.py:194` | Raw literal remains |

The line numbers differ from the issue body because the fixture has changed
since issue creation. The test intent is readable, and the helper
`tests/support/sonar_safe_literals.py:4-5` exposes `ipv4_address()`, but this
target test does not use that helper.

## Quality and external evidence

The targeted unit test passes, while the literal scan still finds all three
address literals. The GitHub connector returned no workflow runs or combined
status checks for the baseline commit. The SonarCloud API endpoint recorded in
the issue was not directly observable in this execution environment; any
external claim that the findings are resolved is therefore `UNVERIFIED`, not
`PASSED`.

## Recommended issue action

Keep #163 open and add a current evidence comment. Implement one focused
test-only correction using named safe literals/constants or the existing narrow
helper while preserving readability; then rerun the targeted test and the full
quality gate. Preserve #159 and #160 as closed duplicates.

Closing reason: not applicable; the original acceptance criteria remain
materially incomplete.

