# Quality Objectives

These objectives are measurable review controls, not certification criteria.
Each review records the observed status and evidence path. Where the project
does not yet maintain a numeric threshold, the target is visibility and
truthful classification rather than an invented number.

| ID | Description | Metric | Target | Evidence source | Review cadence | Owner role |
| --- | --- | --- | --- | --- | --- | --- |
| QO-01 | Architecture boundary compliance | Kept/broken import contracts and architecture-test result | 100% required contracts kept; failures are visible and block completion | `.importlinter`, architecture tests, quality-gate output | Every quality-gate run and monthly review | Lead Architect |
| QO-02 | Quality-gate pass rate | Required gate runs passed / required gate runs executed | Required gates pass before merge; skipped/unavailable is never counted as pass | `QUALITY.md`, `tools/quality_gate.py`, workflow evidence | Every governed change; monthly trend review | Senior Tester |
| QO-03 | Test-coverage visibility | Coverage measurement availability and documented limitation | Coverage status is reported for each release review; no numeric threshold is invented while no coverage tool is configured | Test results, quality-gate evidence, release baseline | Each release baseline and quarterly review | Senior Tester |
| QO-04 | Audit-finding closure rate | Findings with verified closure evidence / findings due for review | No finding is marked closed without evidence and independent review; open rate is visible | `documentation/audit/findings-register.md`, evidence matrix, CAPA records | Monthly audit review | Lead Architect |
| QO-05 | Documentation freshness | Reviewed governed documents with current owner/status/date / documents due | All QMS, audit and workflow documents due for review have an owner and review status | QMS review log, workflow evidence, documentation navigation | Monthly and after behavior changes | Senior Documentation Engineer |
| QO-06 | Secret-leakage prevention | Secret-scan or redaction review findings | Zero committed secrets; any suspected leak is a security CAPA and blocks closure | Diff review, security review, redaction report | Every change; monthly security review | Security Owner |
| QO-07 | Live-evidence completeness | Required live scenarios with redacted evidence / applicable scenarios | Applicable live evidence is explicitly PASS, pending or blocked; no static artifact substitutes for a live run | `documentation/audit/evidence-matrix.md`, live-evidence contract | Before beta/release and after authorized live runs | Senior DevOps Engineer |
| QO-08 | Release-baseline reproducibility | Baseline runs with reproducible inputs and recorded result / baseline runs planned | Every release baseline records inputs, commit, checks, result and remaining risks; failed reproduction blocks release readiness | Release evidence, workflow evidence, quality results | Each release baseline and quarterly review | Workflow Executor |

## Review rules

The owner records the observed value, source path, status and reviewer. A
missing source is `Evidence pending`, `Missing` or another applicable
non-pass state. A skipped test or unavailable external service is never counted
as a successful objective result.

