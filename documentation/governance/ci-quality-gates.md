# CI Quality-Gate Policy

## Canonical local gate

The repository authority is `QUALITY.md`. The canonical local command is:

```bash
python3 tools/quality_gate.py quality
```

It executes these stages in order:

1. verification-policy consistency;
2. Ruff lint;
3. import-linter architecture contracts;
4. hexagonal architecture tests;
5. mypy type checking;
6. the Python unittest suite.

CI should run the same locked environment and publish the command, result,
commit and relevant evidence in the pull request. A local pass does not imply
live, browser, SonarQube or external success.

## Gate expectations

| Gate | Status | Expectation |
| --- | --- | --- |
| Verification-policy consistency | Required now | Detect contradictory verification-state wording. |
| Lint | Required now | Ruff must pass without weakening rules. |
| Architecture lint/tests | Required now | Preserve hexagonal dependency direction. |
| Typecheck | Required now | Mypy must pass for the configured source/test scope. |
| Tests | Required now | Deterministic unittest suite must pass; skips are reported. |
| Security gate | Separate | Run only through an accepted security workflow; do not hide it inside a generic local pass. |
| Live infrastructure smoke | Manual/explicit environment-gated | Never run Incus, Docker, Swarm, network or service bootstrap in default CI. |

Failed, unavailable, skipped without an accepted reason, or unverifiable
required gates are non-pass states and block merge. A live smoke run requires
its own applicability, explicit consent, prerequisites, redacted evidence and
state-specific result.

## Issue #252 CI/release-gate addendum

Issue #252 extends the current CI contract with four required workflow
surfaces. Their presence is planned scope until real GitHub Actions runs
produce evidence:

| Workflow | Required responsibility | Non-success rule |
| --- | --- | --- |
| `python-quality-gate.yml` | PR/push execution of the locked Python quality gate | Any failed, skipped or unavailable stage blocks the required check. |
| `python-compatibility.yml` | Conda matrix for the supported Python versions | Every matrix entry must run; missing entries are not compatible. |
| `sonar_check.yml` | External SonarCloud analysis and status publication | Missing token/status is unavailable, not green. |
| `nightly-classic-live.yml` | Scheduled/manual Classic live chain on a verified self-hosted runner | Missing runner capability, consent or evidence is blocked/unverified, never success. |

The Classic-live workflow is not part of the default hosted quality path. It
requires a protected environment, explicit target ownership, redacted
evidence and a self-hosted runner whose labels and capabilities are proven by a
real run. A workflow file or local test pass does not satisfy this addendum.

## Repository and target checks

| Check | Current repository evidence | Classification |
| --- | --- | --- |
| Python quality gate | `tools/quality_gate.py` and `.github/workflows/python-quality-gate.yml` execute the canonical local gate | Current repository contract; hosted result must be observed. |
| Dependency audit | #127 policy artifacts | Policy/current documentation; execution evidence is separate. |
| SBOM generation | #127 policy artifacts | Target/release evidence when accepted by the release workflow. |
| Container image scan | #127 policy artifacts | Target/release evidence; no scan claim here. |
| SonarQube/SonarCloud | `.github/workflows/sonar_check.yml` consumes the successful quality workflow's coverage artifact and owns only external analysis | Missing token, missing handoff or unavailable status is a failed/non-green external gate. |
| Documentation link/schema check | Governance/documentation review | Recommended target; no new CI job is introduced by #128. |

## Evidence and security boundaries

PR evidence must identify the exact command, environment, commit, result,
skips/blockers and redaction treatment. Raw secrets, tokens, host data and
unredacted logs are forbidden. The default CI path must not create VMs, modify
networking, deploy stacks or bootstrap Infisical, Nexus, Jenkins, Pulsar,
SonarQube, Portainer, Swagger or Traefik.

## Issue #252 S252-13 implementation contract

`python-quality-gate.yml` is the required PR/push check. It installs the
hashed runtime lock, explicitly pinned quality tools, runs
`python3 tools/quality_gate.py quality`, and publishes the generated
`coverage.xml` as a short-lived handoff artifact.

`sonar_check.yml` is triggered only after that workflow completes. It fails
closed when the quality workflow was not successful, the coverage handoff is
missing, or the SonarCloud token is unavailable. It does not run the canonical
Python quality gate a second time and does not present a skipped scan as green.

The workflows are configuration and contract evidence only until an actual
GitHub Actions run provides run ID, commit, trigger, runner, duration,
artifacts and external-gate status. A local test pass does not create that
external evidence.

`python-compatibility.yml` runs the declared Conda matrix for Python 3.12 and
3.13. Each matrix entry creates the environment from `environment.yml`,
installs `requirements.lock` with hash verification, installs the editable
package without dependency drift, runs `pip check` and executes the complete
deterministic unittest contract. A missing or failed matrix entry is not
compatible evidence.
