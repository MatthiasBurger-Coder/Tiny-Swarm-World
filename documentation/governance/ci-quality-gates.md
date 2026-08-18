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
| Python quality gate | `tools/quality_gate.py` and `.github/workflows/python-quality-gate.yml` define it | Current repository contract; hosted result must be observed. |
| Dependency audit | #127 policy artifacts | Policy/current documentation; execution evidence is separate. |
| SBOM generation | #127 policy artifacts | Target/release evidence when accepted by the release workflow. |
| Container image scan | #127 policy artifacts | Target/release evidence; no scan claim here. |
| SonarQube/SonarCloud | `.github/workflows/sonar_external_gate.yml` consumes successful quality runs from the trusted default-branch definition and fails closed | Repository-configured; external result unknown until observed. |
| Documentation link/schema check | Governance/documentation review | Recommended target; no new CI job is introduced by #128. |

## Evidence and security boundaries

PR evidence must identify the exact command, environment, commit, result,
skips/blockers and redaction treatment. Raw secrets, tokens, host data and
unredacted logs are forbidden. The default CI path must not create VMs, modify
networking, deploy stacks or bootstrap Infisical, Nexus, Jenkins, Pulsar,
SonarQube, Portainer, Swagger or Traefik.
