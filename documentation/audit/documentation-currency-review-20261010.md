# Documentation currency review, 2026-10-10

Result: **ALL 17 RECORDED DOCUMENTATION FINDINGS CORRECTED**.
The initial audit identified the findings below; the authorized remediation
updates operator procedures, configuration, architecture, traceability and
status descriptions to match repository evidence. It does not close product
issues, security risks or governance findings, or requalify historical live runs.

Reviewed source: `cd662abdedd001660c059745e9ee739dc13d8fd6`, with documentation
corrections on `docs/current-development-sync-20261010`. The JSON inventory
preserves the initial scan hashes and adds a separate remediation snapshot.

## Scope and method

The inventory covers every tracked artifact under `documentation/`: 172
Markdown/AsciiDoc sources and five JSON artifacts, 177 in total. Root manuals,
nested AGENTS files, Windows bridge documentation and issue templates are also
included. An additional 322 tracked issue-evidence documents were scanned as
supporting historical material. The complete scan inventory contains 511 files.

Every inventoried file was scanned for local links/includes, explicit source
paths, runtime/configuration assertions, verification states, procedure examples
and historical status markers. Semantic review followed the operator, architecture,
configuration, quality, security, traceability, workflow and release claims back
to relevant source, configuration and retained evidence. The accompanying
[coverage inventory](documentation-currency-review-20261010.json) records each
file's content hash, line count and scan categories.

This is a repository consistency audit. Automated coverage does not prove every
sentence or every shell example correct. Literal file targets were checked;
rendered anchor resolution, generated release assets and remote URL availability
were not fully validated. Commands that mutate infrastructure were inspected,
never executed. GitHub issue/check states, external Sonar status, and live hosts
were not queried or inferred from local documents.

## Initial audit findings

All DOC IDs below describe the initial observations, before remediation.

Priorities describe documentation impact: P1 can mislead an operator about
behavior or configuration; P2 affects architecture, verification or status
interpretation; P3 affects navigation or maintenance. They are not new product
security severity ratings.

| ID | Priority | Source and observation | Verified comparison | Required correction |
|---|---|---|---|---|
| DOC-01 | P1 | [Live operation surfaces](../system/live-operation-surfaces.adoc), `prepare_linux.sh` row, describes native-only package preparation and says Incus is not configured. | [prepare_linux.py](../../src/tiny_swarm_world/prepare_linux.py) delegates Python dependencies, Incus preparation and network preparation; the delivered W02/W03/W06 sections of the [bootstrap contract](../contracts/bootstrap.md) cover Linux and WSL2. | Update the supported hosts, staged consent, create/reuse/block behavior and network responsibilities; add the separate Windows preparation surface. |
| DOC-02 | P1 | [Deployment system](../arc42/07_deployment/system.adoc), Nexus bootstrap section, says provider-native Nexus contracts are not yet wired. | Current [deployment composition](../../src/tiny_swarm_world/infrastructure/composition_deployment.py), artifact composition and [Issue #363 final validation](../evidence/issue-363-final-validation-20261003.md) demonstrate implemented contracts and scoped historical live results. | Describe actual wiring; retain target/revision-specific live qualification limits. |
| DOC-03 | P1 | [Usage](../user_guide/usage.adoc), Nexus Bootstrap, and the deployment system list `TSW_PORTAINER_ENDPOINT`, `TSW_NEXUS_STACK_NAME`, `TSW_NEXUS_URL`, `TSW_NEXUS_INITIAL_PASSWORD_PATH`, `TSW_NEXUS_MAX_ATTEMPTS` and `TSW_NEXUS_WAIT_SECONDS` as operator inputs. | These literal names are absent from current product/tools/configuration. The [configuration inventory](../arc42/08_configuration/config-contract-inventory.md), Documentation-Only Or Drifted Keys, already warns about most of them. | Remove unsupported override promises or explicitly classify them as historical/unwired; derive supported inputs from actual owners. |
| DOC-04 | P1 | [Installation](../user_guide/installation.adoc), Docker proxy defaults, presents `TSW_NEXUS_DOCKER_HUB_PROXY_REMOTE_URL` as a configuration assignment. | [_nexus_docker_proxy_remote_url](../../src/tiny_swarm_world/infrastructure/composition_configuration.py) uses the configured LXC registry mirror or a constant; it does not consume that environment name. | Show the default as information, and name only the supported mirror override. |
| DOC-05 | P1 | [Operational readiness checklist](../../OPERATIONAL_READINESS_CHECKLIST.md) assumes one 4-CPU/16-GiB/60-GiB floor, forbids noninteractive execution and describes the older consent/evidence contract. | [native_preparation.py](../../src/tiny_swarm_world/domain/native_preparation.py) has profile/host-specific resource floors. Installer and [Classic runner](../../tools/live/run_classic_acceptance.py) support their explicit noninteractive approval flags and protected XDG evidence roots. | Split readiness by profile, host and entrypoint; distinguish any retained legacy consent contract from supported installer/Classic execution. |
| DOC-06 | P1 | [Deployment view](../arc42/07_deployment_view.adoc), lines 109 and 185, names the external ingress network `tiny_swarm_world_ingress`. | [Traefik compose](../../infra/config/compose/traefik/docker-compose.yml) and service-access compose use `service_access_link`, including Traefik's Swarm provider network. | Correct the network name from the effective committed compose contracts. |
| DOC-07 | P2 | [Simple secret bootstrap](../arc42/08_configuration/rc1-simple-secret-bootstrap.md), normal installation step 4, and [Infisical silent setup](../arc42/08_deployment_configuration/infisical-silent-setup.adoc), Reset Behavior, generalize reset/setup without the native exception. | [InstallationService](../../src/tiny_swarm_world/application/services/installation.py) skips reset for native reconciliation; bootstrap rejects native `--confirm-reset`. | Distinguish native reconciliation, WSL2 confirmed reset and a separately requested native reset. Qualify the [installer console example](../user_guide/installer-console-output.md) as WSL2 and add the native mode. |
| DOC-08 | P2 | [Traceability coverage](../traceability/test-coverage-map.md) presents 1761 tests, 28 skips and 622 typed files as current, names the removed `tests/live/test_post_install_browser_live.py`, and links to absent `.tiny-swarm/evidence/issue-150/test_results.md`. The [traceability matrix](../traceability/traceability-matrix.md) also references removed issue workflow paths. | The canonical browser suite is under [tests/e2e/classic](../../tests/e2e/classic/). The literal linked evidence file and named workflow files do not exist in this checkout. | Attribute old results to a dated candidate, replace stale navigation with retained sources, and avoid inventing current counts or missing evidence. |
| DOC-09 | P2 | [CI quality policy](../governance/ci-quality-gates.md) and [branch protection policy](../governance/branch-protection.md) omit the complexity stage from the full gate description. | [QUALITY.md](../../QUALITY.md) and [quality_gate.py](../../tools/quality_gate.py) place `complexity` immediately after `verification-policy`. | Synchronize the gate sequence and gate table with the authoritative runner. |
| DOC-10 | P2 | [ASVS mapping](../security/owasp-asvs-mapping.md), [admin surface model](../security/admin-surface-rbac.md), [security controls](../security/security-controls.md) and [SoA](../security/statement-of-applicability.md) still describe route/TLS/dashboard design or the evidence contract as future work for #126/#150/#125. | Current [Traefik configuration](../../infra/config/compose/traefik/docker-compose.yml), [TLS decision](../arc42/09_decisions/adr-traefik-managed-or-operator-ca.adoc), ASVS file, evidence contract and scoped [RC1 security evidence](../security/rc1-classic-security-evidence.md) exist. | Separate delivered configuration/policy from unverified runtime controls and genuinely open RBAC, rotation or exposure work. Existing artifacts alone do not close risks. |
| DOC-11 | P2 | [Remediation plan](remediation-plan.md) and [evidence matrix](evidence-matrix.md) mark multiple documentation deliverables as planned while their maintained QMS, ISMS, ASVS, traceability and audience files exist. The [findings register](findings-register.md) retains older missing-document descriptions. | The named artifacts are present under `documentation/`; later scoped release/evidence records also exist. | Reconcile artifact-presence status and dated finding descriptions with actual review evidence. Do not automatically mark governance or audit findings Closed. |
| DOC-12 | P2 | [Root README](../../README.md) and documentation entry pages describe RC1 qualification as still in progress; the [live validation manual](../manuals/live-validation-manual.md) and [live evidence map](../traceability/live-evidence-map.md) give an unqualified current missing-consent state. | [RC1 decision](../release/rc1-decision.md) records `RC1_ACCEPTED` for named September candidates. [Issue #363](../evidence/issue-363-final-validation-20261003.md) records October lifecycle results. Later bootstrap changes are not thereby live-qualified. | Present dated acceptance separately from current development/qualification gaps. Never convert historical acceptance into a pass for the current tree. |
| DOC-13 | P2 | [Vaultwarden EPIC](../arc42/01_introduction/service-access-dashboard-vaultwarden.md) is labeled `ACTIVE_BASELINE_EXTENSION`; the [Vaultwarden ADR](../arc42/09_decisions/adr-service-access-dashboard-vaultwarden.adoc) still describes Vaultwarden in its implemented compose assets. Other introduction EPICs call old versions of `workflow.md` active. | [services.yml](../../infra/config/services.yml), installation plan and current compose select Infisical. The current workflow is issue #355, not those historical versions. [Risks and debt](../arc42/11_risks_and_debt.adoc) already identifies the Vaultwarden baseline as historical. | Add explicit historical/current applicability and links to current credential contracts. Preserve the original requirement/decision text; any change to requirement intent needs its owner. |
| DOC-14 | P2 | [Dependency map](../arc42/05_analysis/arch-03-01-dependency-map.md), [violation inventory](../arc42/05_analysis/arch-03-01-violation-inventory.md) and [dead-path audit](../arc42/05_analysis/arch-03-17-dead-path-audit.md) mix baseline findings with apparent current ownership, including CLI rendering and installer process creation at package root. | [__main__.py](../../src/tiny_swarm_world/__main__.py) delegates to the CLI dispatcher; [resulting architecture](../arc42/05_analysis/arch-03-21-resulting-architecture.md) documents the extracted installation service/adapters. Some composition compatibility debt is explicitly retained. | Label original inventories as dated snapshots and map each obsolete owner/finding to current disposition; retain actual outstanding debt. |
| DOC-15 | P3 | [arc42 decision chapter](../arc42/09_architecture_decisions.adoc) does not assemble the accepted native installation lifecycle, Classic update or Windows/WSL lifecycle preparation ADRs, nor the command-runner decision. | The four standalone files exist in `arc42/09_decisions/`, with their own accepted status and applicability. | Include or explicitly link each decision with its status; avoid treating a proposal or historical qualification as current implementation proof. |
| DOC-16 | P3 | [Evidence matrix](evidence-matrix.md) assigns `EVD-121-022` both to the hexagonal test and to the audit-summary snapshot. | Two rows in the same stable-ID table use the same ID. | Give the snapshot a unique ID and migrate any consumers while retaining traceability. |
| DOC-17 | P3 | [Changelog](../../CHANGELOG.md) says all notable changes are recorded, but its Unreleased section omits the current native lifecycle, Incus preparation, WSL lifecycle/capacity and network preparation deliveries. | Recent local Git history records #463 and #467–#470; the changelog's last change predates these deliveries. | Add concise unreleased entries tied to actual behavior and qualification limits; do not create a release or tag. |

## Historical material and non-findings

- Archived migration and agent-split plans explicitly identify pre-removal
  Multipass paths. Those references are historical evidence, not supported
  provider instructions, and should remain attributed to their baseline.
- Earlier failed/incomplete Issue #363 records point to the final validation
  report. Preserving the original failed status is correct.
- RC1 release decisions and scan records carry candidate SHAs. Their age is
  not itself an error; the defect is describing them as universal current
  readiness, or ignoring them in an undated current-status page.
- The Windows release manifest is a generated distribution asset. Its absence
  from the source checkout is not a broken-reference defect: the guide explains
  how to produce and package it.
- Missing paths explicitly marked removed, planned, expected, forbidden or
  archival are not treated as broken current implementation references.
- Public disposable catalog credentials are intentionally documented. Policy
  wording must distinguish these from real operator secrets; their presence
  alone is not reported as a newly discovered credential leak.
- Skill discovery counts match the registry: 132 project entrypoints, six
  Codex fallback entrypoints, and no missing required project skills. At initial review, governing
  hashes matched committed HEAD; the authorized README correction required a
  refresh, which was completed during remediation.
- Completed issue #355 workflow/context records are historical execution
  records. Changed governing hashes and a different development branch make
  them unsuitable for blindly resuming execution; they should not be regenerated
  as part of this documentation audit.

## Initial audit validation and limits

- `python3 tools/quality_gate.py verification-policy`: PASS. This narrow check
  does not detect all semantic drift listed above.
- All five tracked documentation JSON files parse successfully.
- Literal local Markdown/AsciiDoc links and includes across the scan: one
  missing target, the Issue #150 evidence link in DOC-08. Source paths mentioned
  in inline code were checked separately and classified by historical/planned
  context; not every missing mentioned path is a defect.
- Source/configuration comparisons were static. No Incus, Docker/Swarm,
  networking, credentials, browser, release, commit, push or remote setting
  operation was performed.
- No full quality gate or AsciiDoc/PlantUML rendering was run for this
  documentation-only audit. The detected Asciidoctor is a Windows-mounted Ruby
  tool; a qualified Linux rendering setup was not established.
- External settings, current issue state, remote links and current live
  readiness remain unverified. The report relies on retained repository
  evidence only for its stated historical candidates.

## Original correction groups (now implemented)

1. Operator behavior and configuration: DOC-01–07, owned by documentation with
   Python/DevOps source review; synchronize the safety-critical procedure pages.
2. Quality and traceability: DOC-08–09 and DOC-12, owned by Tester and
   Documentation; attribute every result to its executed candidate.
3. Security and audit applicability: DOC-10–11 and DOC-16, owned by Security,
   QMS/Audit and Documentation; review disposition evidence before status changes.
4. Architecture/history and navigation: DOC-13–15 and DOC-17, owned by Architect,
   Requirement Engineer and Documentation; preserve historical decisions and
   distinguish them from current implementation.

## Remediation review, 2026-10-10

| Findings | Correction and verification |
|---|---|
| DOC-01–07 | Operator and deployment pages now describe staged Linux/WSL preparation, actual Nexus wiring and supported overrides, profile-specific resources, `service_access_link`, and native reconciliation versus confirmed WSL reset. Procedures were compared with their source/configuration owners. |
| DOC-08–09 | Traceability distinguishes source mapping from executed proof; missing original evidence is identified, current test paths are mapped, and both CI policies include the complexity gate. |
| DOC-10–11 | Security and audit pages distinguish delivered artifacts and scoped qualification from open effectiveness, RBAC, rotation and closure work. Existing risk/finding dispositions were preserved. |
| DOC-12 | Entry pages attribute RC1 acceptance and lifecycle results to their dated candidates; changed bootstrap and new targets require their own verification. |
| DOC-13–14 | Retained EPIC/ADR intent and original architecture findings are preserved as historical baselines, with current applicability and ownership dispositions. |
| DOC-15–16 | The decision chapter includes the four omitted ADRs. The audit-summary evidence ID is now `EVD-121-023`; `EVD-121-022` remains the architecture test. |
| DOC-17 | Unreleased changelog entries describe delivered host preparation and lifecycle behavior without creating a release. |

Related security applicability pages were reconciled consistently. The skill
registry's governing README hash was refreshed after the authorized edits.
All changes are documentation or documentation inventory metadata; product
source and configuration were not changed.

## Remediation validation and limits

- `python3 tools/quality_gate.py quality`: PASS on Linux with Python 3.14.4,
  against the source baseline above plus this documentation working tree.
  Verification-policy, complexity (312 orchestration modules), Ruff, import-linter
  (seven kept contracts), architecture tests (43), Mypy (796 source files)
  and full unittest discovery all passed.
- Full regression: 2529 tests in 613.443 seconds, 18 skipped.
  These skips and this local result do not establish live or external success.
- Literal relative Markdown links and AsciiDoc links/includes: 399
  targets checked, zero missing. Attribute-expanded targets, rendered anchors
  and remote URLs are outside this literal-target check.
- All 6 documentation JSON artifacts parse successfully; all eight
  registry governing hashes match their current files.
- `git diff --check`: PASS. No product source/configuration changes, live
  infrastructure mutations, commits, pushes or remote settings changes.

The scope limitations above still apply. No current live, Selenium, external
SonarQube or remote branch-protection success is claimed. Missing historical
packages and open risk/control effectiveness reviews remain explicitly visible.
