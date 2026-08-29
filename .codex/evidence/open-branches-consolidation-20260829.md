# Open-Branches Consolidation Report

Date: 2026-08-29
Integration branch: `integration/open-branches-consolidation`
Authoritative baseline: `origin/main` at `b7b1f23ab7e6bf6125aa1285c0bd371f52738df`

## Consolidation status

`CONSOLIDATION STATUS: BLOCKED`

The repository has one coherent local implementation on the integration
branch, but the requested GREEN gate is not satisfied: exact-candidate
external CI/Sonar evidence, Native Linux lifecycle evidence and an independent
final issue-completion audit remain open. The existing Issue #252 evidence
explicitly records `INCOMPLETE`; historical live evidence was not transferred
to this new candidate.

## Branch inventory

| Branch | Purpose and evidence | Disposition |
| --- | --- | --- |
| `origin/main` / `main` | Authoritative current baseline; contains the trusted external Sonar bootstrap from PR #266. | KEEP as base |
| `feature/classic-public-beta-rc1-stabilization` / PR #265 | Issue #252 remediation: R01–R08, TLS, Traefik secrets, readiness, host checks, live workflow, tests, docs and evidence; 33 commits ahead of the baseline. | KEEP + ADAPT; integrated selectively |
| `ci/remove-legacy-sonar-pr-gate` / PR #267 | Removes the legacy `sonar_check.yml` authority and pins the trusted Sonar revision to the exact workflow-run SHA; 2 commits. | KEEP + RECONCILE |
| `feature/workflow-issue-252-remediation-20260823` | Workflow authoring branch; its committed history is an ancestor/subset of PR #265. | SUPERSEDED as an independent source; represented by PR #265 |
| `docs/workflow-issue-252-ci-live-addendum-20260818` | Documentation addendum; its committed history is an ancestor/subset of PR #265. | SUPERSEDED as an independent source; represented by PR #265 |
| `preserve/issue-252-candidate-20260823` | Preserve branch whose committed history is an ancestor/subset of PR #265; its dirty worktree was reviewed separately. | SUPERSEDED as an independent source; worktree preserved |
| `release` | Stale release baseline, 310 commits behind `origin/main`; not an open development source. | EXCLUDED / DROP from consolidation |
| `origin/public/main` | Separate stale public reference, 151 commits behind `origin/main`; not authoritative for this repository. | EXCLUDED / DROP from consolidation |
| `origin/ci/sonar-trusted-bootstrap` | Former PR #266 source; already merged into `origin/main` and removed by fetch/prune. | ALREADY REPRESENTED |

All original branches and worktrees remain intact. No remote branch was
deleted, closed, force-pushed or merged by this consolidation.

## Change matrix

| Source change | Decision | Reason and evidence |
| --- | --- | --- |
| R01 canonical external-precedence / managed-fallback TLS resolver | KEEP | Accepted `adr-traefik-managed-or-operator-ca.adoc`; resolver validates CA/leaf/SAN/expiry/key pairing, persists managed state and exposes one contract. |
| R02 Traefik TLS secret-pair ownership, rollback and operator htpasswd pre-apply verification | KEEP + ADAPT | Correctly reuses ports and pre-apply boundaries; retained the newer labelled logical pair and state-specific verification. |
| R03 bounded Incus `admin waitready` | KEEP | Fixes the observed WSL2 startup race before version/info; local regression and branch evidence cover the ordering. |
| R04 managed-manager Docker/storage artifact probes | KEEP | Aligns readiness with the selected Incus/LXC execution backend and fails closed when unresolved. |
| R05 read-only Native Linux kernel prerequisite verification | KEEP | Reads procfs without mutating host state; local tests distinguish active, missing, disabled and read-error states. |
| R06 bounded Classic post-install readiness | KEEP | Uses the existing opt-in E2E runner, one bounded deadline and redacted evidence; no default live mutation. |
| R07/R08 architecture, requirement, traceability and local acceptance evidence | KEEP + ADAPT | Preserved, but statuses remain local/incomplete where external or host evidence is absent. |
| PR #267 legacy Sonar removal and exact revision pin | KEEP + RECONCILE | Applied after the main trusted workflow; updated tests, workflow metadata and docs to `sonar_external_gate.yml`. |
| Older `sonar_check.yml` references from PR #265 workflow/docs/tests | RECONCILE | Replaced references with the single current trusted external workflow; no duplicate Sonar authority remains. |
| Preserve direct `openssl req -x509` generation in `StackPrerequisiteRegistry` | DROP | Contradicts the accepted ADR and the R01 resolver: it creates a second self-signed cert lifecycle, bypasses CA/leaf validation and writes `traefik-live-ca-current.pem` independently. The canonical registry now consumes the resolved contract bytes. |
| Preserve old `LxcDockerManagerReadinessProbe` / `LxcDirectoryReadinessProbe` and old Native Linux semantics | SUPERSEDED | Later R04/R05 implementations use typed managed probes and redaction-safe state classifications; retaining the older variants would regress the selected-backend and no-mutation contracts. |
| Preserve older live readiness implementation | SUPERSEDED | R06 contains the later canonical resolver join, global deadline and failure evidence model. The older polling variant would duplicate or bypass that contract. |
| Preserve untracked local RC1 evidence files from the dirty preserve worktree | DROP from integration input | They are not branch commits, overlap the committed Issue #252 evidence, use historical SHAs, and some contain host/IP details prohibited for tracked canonical evidence. They remain untouched and recoverable in the preserve worktree. |
| `release` and `origin/public/main` implementation histories | DROP from integration input | They are stale/non-authoritative baselines and would reintroduce unrelated historical divergence. |

## Three-Amigos conflict review

### Product / requirement

Issue #252 requires one current RC1 implementation, honest failure states and
preservation of valid regression coverage. PR #265 supplies the relevant
remediation slices. PR #267 is the newer CI intent and removes a duplicate
Sonar path. The final matrix still requires exact-candidate live and external
evidence, so local green tests do not close RC1.

### Development / architecture

The accepted managed/operator CA ADR has precedence over the older
existing-CA-only ADR. Operator CA material wins when complete; otherwise the
resolver owns persistent managed CA plus a separately signed leaf. Installer,
runtime, Traefik secret preparation and E2E obtain the same resolved trust
contract. Traefik does not generate a CA, and the stack registry does not
create an alternate certificate path.

The integration preserves the Python hexagonal boundaries: domain code models
the contract, application code uses ports, and OpenSSL/Docker/LXC details stay
in infrastructure adapters. The CI split likewise has one quality authority
and one trusted external Sonar authority.

### Quality / testing

Valid tests from the remediation slices were retained. Contract tests were
adapted to the actual current workflow name and now verify exact candidate SHA
checkout, Sonar revision pinning, quality-gate waiting and the absence of a
second local quality installation in the external job. Assertions were not
weakened to accommodate the consolidation.

## Architecture decisions

1. `adr-traefik-managed-or-operator-ca.adoc` is the active decision; the
   existing-CA-only ADR remains history and is marked superseded.
2. `TSW_TRAEFIK_CA_CERT_PATH`, `TSW_TRAEFIK_TLS_CERT_PATH` and
   `TSW_TRAEFIK_TLS_KEY_PATH` form the external input tuple. Incomplete input
   fails closed; otherwise the resolver uses protected managed state.
3. `TSW_LIVE_TLS_CA_BUNDLE` is only a validated compatibility alias to the
   resolver's selected trust bundle, not a second CA authority.
4. `sonar_external_gate.yml` is the only external Sonar workflow. It consumes
   the successful locked quality run, checks trusted provenance and metadata,
   checks the coverage handoff and waits for the external quality gate.
5. Native Linux host preparation remains read-only. Operator kernel activation
   and persistence are documented actions, not automation side effects.

## Verification evidence

Executed on the integration branch:

- YAML parsing of all `.github/workflows/*.yml`: `PASS`.
- JSON parsing of `documentation/workflow/context-pack.json`: `PASS`.
- CI contract tests: `7` passed.
- `python3 tools/quality_gate.py test`: `1834` passed, `18` expected skips.
- `python3 tools/quality_gate.py quality`: `PASS` — policy consistency,
  Ruff, 3 import-linter contracts, 18 architecture tests, Mypy and `1834`
  tests with `18` expected skips.
- `git diff --check`: `PASS` for each edited slice.
- Repository evidence under `.tiny-swarm/evidence/issue-252/` explicitly
  records local verification as distinct from live/external verification.

Not established on this exact consolidation candidate:

- GitHub Actions runs for Python quality, Conda compatibility, trusted Sonar
  and the protected Classic-live workflow.
- Native Linux lifecycle matrix.
- A fresh exact-candidate WSL2/Native-Linux live installation and full RC1
  acceptance rerun.
- Independent final Issue #252 completion-auditor PASS.

The full local quality gate is green, but it does not upgrade missing
external/live states. None of those states is inferred from this local test
pass.

## Remaining risks and handoff

- The integration branch is locally coherent but not GREEN under the supplied
  completion gate because mandatory live/external evidence remains open.
- Existing source branches remain the recovery boundary and must not be
  deleted without explicit approval.
- The next safe action is to run the full local quality gate on this exact
  branch, then obtain the required protected CI/live evidence before any PR
  merge or source-branch cleanup.
