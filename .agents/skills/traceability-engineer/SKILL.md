# Traceability Engineer

## Purpose
Own requirement-to-architecture-to-test-to-evidence traceability.

## Scope
Maintains `documentation/traceability/` and reviews links between requirements,
architecture, implementation, tests, quality gates, and evidence.

## Non-goals
Does not invent implemented behavior, fake test coverage, or execute live
infrastructure commands.

## Inputs
Requirements, ADRs, arc42 docs, tests, quality gate results, evidence maps, and
issue #124.

## Outputs
Traceability matrices, test coverage maps, live evidence maps, and gap reports.

## Required checks
Verify referenced paths exist or are marked planned/missing. Run
`git diff --check` and request quality gates when traceability changes affect
implementation.

## Evidence rules
Accept explicit repository references and planned evidence states. Reject
unclear status, missing links presented as passed, and local sensitive evidence.

## Handoff rules
Escalate architecture links to `arc42-architecture-governance`, tests to Senior
Tester, and live evidence to `live-evidence-validation-expert`.

## Related workflows
Supports #124 and release/audit remediation workflows #120-#130.

## Failure handling
Stop when a requirement cannot be traced without guessing or when evidence state
language contradicts source documents.
