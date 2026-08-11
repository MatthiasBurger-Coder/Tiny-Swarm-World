# Slice Consolidation — I156-S06

Workflow: issue-156-20260809
Workflow version: issue-156-v1.0.0
Slice ID: I156-S06
Slice title: Remove or classify unsupported legacy direct-port artifacts

## Result

- Serial cleanup execution completed after I156-S05.
- No real subagent tool was visible; explicit role-based fallback review was completed.
- `infra/config/services.yml` now states that registry-backed published values are resolved centrally and compatibility values are explicit metadata only.
- Arc42 and network documentation now distinguish internal Compose targets, registry-backed published ports, Traefik ingress and the retained service-access `8086` compatibility/rollback path.
- The stale Arc42 Pulsar `8087` and Swagger published `8084` claims were corrected to `14001/14080/14081` and `16080/16081` respectively, with internal targets documented separately.
- No valid internal target was removed, no unsupported service was invented, and no RabbitMQ artifact exists in active `infra/config`.
- No live infrastructure command was executed.

## Role results

- Senior System Architect: approved target-vs-published corrections and retention of the valid compatibility listener.
- Senior Requirement Engineer: traced the retained `8086` value to `service-access-legacy-http` with `COMPATIBILITY` exposure.
- Senior DevOps Engineer: confirmed Apache Pulsar remains the active messaging path and no runtime mutation is needed.
- Senior Tester: verified compatibility metadata, target preservation, registry classifications and RabbitMQ absence.
- Documentation review: synchronized only verified static facts and preserved local-vs-live evidence wording.

## Verification

- `git diff --check`: passed.
- Focused Compose/config and legacy-surface tests: `67` passed.
- Full WSL quality gate: passed.
  - verification policy: PASS
  - Ruff: PASS
  - import architecture: `3` kept, `0` broken
  - architecture tests: PASS
  - mypy: no issues in `600` source files
  - full test suite: `1707` passed, `28` skipped
- External SonarQube state: UNVERIFIED; no external success claim is made.

## Changed files

- `infra/config/services.yml`
- `documentation/system/network.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `.codex/evidence/slice-I156-S06-distribution.md`
- `.codex/evidence/slice-I156-S06-consolidation.md`

## Handoff

I156-S06 is complete and ready for I156-S07. The next slice must run the complete port-contract regression suite and keep every requirement mapped to passing local checks or an explicit classified blocker.
