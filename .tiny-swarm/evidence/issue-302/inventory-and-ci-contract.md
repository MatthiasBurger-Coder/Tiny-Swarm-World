# Reconciled assets, service scope and CI contract

| Asset | Classification | Current proof / reason |
|---|---|---|
| tools/install_debugger.py | REUSE_AS_IS | Read-only local/live diagnostics; final-local-baseline and both fresh runners |
| tools/preflight.py | REUSE_AS_IS | Canonical static preflight; missing environment intentionally fails, configured repeat passes |
| tools/quality_gate.py | REUSE_AS_IS | Six canonical stages; current full gate and exact integrated hosted quality |
| tools/security_gate.py | REUSE_AS_IS | R04 dependency/SBOM/three-Dockerfile configuration scans |
| tools/live/run_classic_acceptance.py | EXTEND | Existing thin environment/phase orchestration now invokes canonical authenticated tests after each mutation |
| remaining tools/live utilities | REUSE_AS_IS / NOT_APPLICABLE | Protected runtime-path helper reused; legacy Windows bridge/VM utilities remain outside product expansion |
| former tests/integration/test_post_install_browser_live.py and tests/live wrappers | MOVE_TO_TESTS | S252-02 migration; one tests/e2e/classic implementation; routing-only integration tests remain |
| tests/e2e/classic lifecycle contracts | WRAP_IN_RC1_SCENARIO | Existing lifecycle, update, fail-closed, redaction and canonical authentication tests; no second assertion framework |
| former sonar_check.yml | REPLACE_WITH_REASON | One sonar_external_gate.yml consumes successful Python coverage and analyzes the actual trigger SHA with waited gate |
| python-quality-gate.yml | REUSE_AS_IS | PR and main push, Python 3.12, hashed lockfile, pinned tools, six-stage canonical quality, coverage artifact |
| python-compatibility.yml | REUSE_AS_IS | Authoritative environment.yml and pyproject scope 3.12/3.13, setup-miniconda, separate jobs, fail-fast false, canonical unittest discovery |
| nightly-classic-live.yml | EXTEND | Existing protected self-hosted strategy, cron/manual, explicit approval and owner, serialized target, 10/45-minute bounds, canonical 14-operation chain |

The historical S252-01 update-via-setup finding is superseded by canonical
`platform update` and `platform update --recover`, implemented and tested under #297.
The old test-layout decision and migration remain actual historical decisions,
not fresh live claims. Files under tools orchestrate commands and redact their
results; assertions are canonical tests under tests/e2e/classic and domain/
application regression suites. Private continuity probes compare fixtures and
emit bounded observations; they do not replace canonical browser/API assertions.

All nine selected service-access stacks are RC1_REQUIRED: service-access,
Portainer, Traefik, Nexus, Jenkins, Pulsar, SonarQube, Swagger and Infisical.
The concrete catalog also includes their support databases, cache, agents and
the completed Pulsar manager bootstrap task. R08 inventories all 20 running
task images per host; the bootstrap one-shot is not mistaken for an unhealthy
long-running service. Vaultwarden is NOT_IN_CLASSIC_PROFILE. There is no extra
RC1_OPTIONAL stack selected in this profile. Incus/LXC manager plus two workers,
Docker on each node, Ready/Active Swarm and routing/secrets/artifacts dependency
order are verified by canonical setup/platform results and post-phase suites.

## CI invariants and observed authority

All four workflows are separately observable. YAML uses least-privilege contents
read; Sonar additionally reads Actions coverage. Third-party actions are pinned
to full commits; successful candidate runs resolve and execute those actions.
No duplicate Ruff/mypy configuration or second Sonar analysis is introduced.
Canonical commands exist and their CLI/CI contracts are tested in
tests/test_ci_workflow_contract.py and tests/tools/test_classic_live_runner.py.
Conda uses explicit shell failure propagation and fail-fast false; no
continue-on-error masks a failed version. Quality propagates the child command's
nonzero exit. The deliberate local failure probe and actual controlled blocked
hosted dispatch are distinct evidence in failure-semantics.json and R05.

Nightly has a real cron declaration and actual manual lifecycle execution;
no claim is made that a cron-triggered run executed. Concurrency is repository
target-wide with cancel-in-progress false; qualification and execution timeouts
are bounded. Hosted artifacts contain only redacted summaries/checksums; raw
environment and command output remain excluded. Setup failure propagates into
the final state and dependent phases stop. Earlier failed hosted attempts and
cancelled intermediate documentation push checks are retained as non-success.

Intended required checks are documented in documentation/governance/ci-quality-gates.md:
Python Quality Gate / Locked Python quality gate; Python Compatibility / Conda
Python 3.12 and 3.13; SonarCloud Trusted External Gate / SonarCloud external
analysis; Nightly Classic Live / Execute Classic live chain. Actual PR Sonar
status is SonarCloud Code Analysis; its workflow's actual SCM revision is also
read, because workflow_run metadata can identify a different main revision.
No branch-protection rule is changed by this evidence audit.
