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
