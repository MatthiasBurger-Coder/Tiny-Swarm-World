# CI Quality-Gate Policy

## Canonical local gate

The repository authority is `QUALITY.md`. The canonical local command is:

```bash
python3 tools/quality_gate.py quality
```

It executes these stages in order:

1. verification-policy consistency;
2. complexity guardrails;
3. Ruff lint;
4. import-linter architecture contracts;
5. hexagonal architecture tests;
6. mypy type checking;
7. the Python unittest suite.

CI should run the same locked environment and publish the command, result,
commit and relevant evidence in the pull request. A local pass does not imply
live, browser, SonarQube or external success.

## Gate expectations

| Gate | Status | Expectation |
| --- | --- | --- |
| Verification-policy consistency | Required now | Detect contradictory verification-state wording. |
| Complexity | Required now | Preserve the reviewed complexity baseline and exception policy. |
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
| `sonar_external_gate.yml` | Trusted external SonarCloud analysis and status publication | Missing token/status is unavailable, not green. |
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

## Issue #252 S252-13 implementation contract

`python-quality-gate.yml` is the required PR/push check. It installs the
hashed runtime lock, explicitly pinned quality tools, runs
`python3 tools/quality_gate.py quality`, and publishes the generated
`coverage.xml` as a short-lived handoff artifact.

`sonar_external_gate.yml` is triggered only after the trusted default-branch
quality workflow completes. It fails closed when the quality workflow was not
successful, the coverage handoff is missing, or the SonarCloud token is
unavailable. It does not run the canonical Python quality gate a second time
and does not present a skipped scan as green.

The workflows are configuration and contract evidence only until an actual
GitHub Actions run provides run ID, commit, trigger, runner, duration,
artifacts and external-gate status. A local test pass does not create that
external evidence.

## Stable status-check names

The intended branch-protection check names are the workflow and job display
names below. Matrix entries remain independently required checks:

| Responsibility | Intended status check |
| --- | --- |
| PR/push quality | `Python Quality Gate / Locked Python quality gate` |
| Python 3.12 compatibility | `Python Compatibility / Conda Python 3.12` |
| Python 3.13 compatibility | `Python Compatibility / Conda Python 3.13` |
| Python 3.14 compatibility | `Python Compatibility / Conda Python 3.14` |
| Trusted SonarCloud result | `SonarCloud Trusted External Gate / SonarCloud external analysis` |
| Classic live qualification | `Nightly Classic Live / Execute Classic live chain` |

Only checks from an observed workflow run may satisfy the corresponding RC1
gate. A missing, skipped, blocked, failed or unavailable check is not green
evidence.

`python-compatibility.yml` runs the declared Conda matrix for Python 3.12,
3.13 and 3.14. Each matrix entry creates the environment from `environment.yml`,
installs `requirements.lock` with hash verification, installs the editable
package without dependency drift, runs `pip check` and executes the complete
deterministic unittest contract. A missing or failed matrix entry is not
compatible evidence.

`nightly-classic-live.yml` is intentionally separate from the hosted quality
path. It accepts only the `self-hosted`, `linux`, `tsw-classic` runner label,
requires a protected `tiny-swarm-world-classic-live` environment and explicit
target ownership, and invokes `tools/live/run_classic_acceptance.py` with live
approval. The runner must already hold the private ignored operator env file;
the workflow never prints or uploads it. Missing runner capability, approval,
ownership, credentials or redacted evidence is a blocked/non-success state.

### Classic runner availability on WSL

The WSL runner must run as a persistent service rather than an interactive
`run.sh` process. The protected host uses the systemd user unit
`actions.runner.tsw-classic.service` under `~/.config/systemd/user/`. Its
working directory is the runner installation and its executable is the
installation's `bin/runsvc.sh`, invoked through `/bin/bash`. The unit is enabled
for `default.target`, with `Restart=on-failure`, `RestartSec=15`, and a limit of
five starts per 300 seconds. It retains the runner's service shutdown settings:
`KillMode=process`, `KillSignal=SIGTERM`, and `TimeoutStopSec=5min`.

Check availability from the runner owner's Linux shell:

```bash
systemctl --user is-enabled actions.runner.tsw-classic.service
systemctl --user is-active actions.runner.tsw-classic.service
loginctl show-user "$USER" -p Linger
```

Enable user lingering with `loginctl enable-linger "$USER"` so the service
starts with the user manager at boot and survives logout. WSL must remain
running; this service cannot start a stopped WSL distribution or Windows host.
Use `systemctl --user restart actions.runner.tsw-classic.service` for a
controlled restart only when the runner is idle and pending live runs have
been reviewed. Review diagnostics locally with
`journalctl --user -u actions.runner.tsw-classic.service`; do not publish raw
runner logs or registration credentials.

If a job has no executed steps and reports that it waited 24 hours for a
runner, inspect runner availability before investigating the live tests.
GitHub can delete registrations after prolonged inactivity. If the listener
reports a deleted registration, remove its stale local configuration using
the runner's `config.sh remove`, then register it again with a fresh GitHub
registration token and the original name and labels. Keep tokens outside Git
and restart the service after registration. Verify both the local service and
GitHub's `online` status; neither proves that the Classic live chain passed.

The repository variables `TSW_CLASSIC_UPDATE_FROM_IMAGE` and
`TSW_CLASSIC_UPDATE_TO_IMAGE` must identify distinct, available images in the
protected target's registry. A historical test tag can disappear while its
GitHub variable remains configured. A missing target image causes Swarm tasks
to be rejected and the update verification to fail. Restore the selected
service with the canonical `platform update --recover` command and verify its
convergence before repeating a failed live chain. Select an available,
qualified compatibility image for the next run; a packaging compatibility
test does not establish a Jenkins binary-version upgrade.
