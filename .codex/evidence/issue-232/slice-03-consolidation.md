# Issue #232 — Slice 03 consolidation

- Workflow: `issue-232-20260808`
- Slice: `03` — Profile inventory, Compose alignment and override resolution
- Decision: ACCEPTED for checkpoint commit.
- Execution mode: serial role-based fallback; no callable Codex subagents were
  available and no live infrastructure was used.

## Implemented contract

- `ComposeServiceDefinition` now carries the effective image reference alongside
  service name and published ports.
- `PortComposeFileRepository` exposes a typed `ArtifactImageInventory` for the
  selected `ServiceStackProfile`.
- `ComposeFileRepositoryYaml` resolves Compose `${TSW_*_IMAGE:-default}` values
  and artifact contracts through the same resolver. The resolver handles tags,
  digests and untagged override input consistently; implicit `latest` remains a
  later static validation failure.
- Profile inventories include only contracts selected by that profile. The
  default profile excludes Infisical and service-access requirements; the
  service-access profile includes all configured stack image requirements.
- The canonical contract set now covers every image in the selected Compose
  profiles, including Portainer, its agent, Nexus and the digest-pinned
  Swagger API image.
- All 11 repository-supported `TSW_*_IMAGE` override variables are enumerated
  and tested against artifact contract resolution.
- The deployment composition passes the new Traefik and Pulsar bootstrap image
  values through the existing stack environment boundary.

## Role-based review findings

| Reviewer | Decision | Evidence |
|---|---|---|
| Senior Python Automation Developer | accepted | Compose inventory, override and composition tests passed |
| Senior Tester | accepted | 149 focused tests and full discovery pass |
| Senior System Architect | accepted | YAML remains in infrastructure; application receives typed inventory; architecture gates passed |
| Senior Requirement Engineer | accepted | REQ-001/002/004/005/006/014/015/016/017 mapped to this slice; later preflight/live requirements remain open |
| Senior DevOps / security review | accepted | immutable digest/tag contracts and implicit-latest validation remain enforced |

## Verification

- Focused Compose/domain/composition tests: `149` tests, `OK`.
- `python3 tools/quality_gate.py lint`: PASS.
- `python3 tools/quality_gate.py arch-lint`: PASS, 3 contracts kept, 0 broken.
- `python3 tools/quality_gate.py arch-tests`: PASS, 18 tests.
- `python3 tools/quality_gate.py typecheck`: PASS, no issues in 531 source files.
- `python3 tools/quality_gate.py quality`: PASS; verification policy, lint,
  architecture, typecheck and test stages all reported success. The full test
  stage reported `1,608` tests, `28 skipped`, and `OK` in 109.812 seconds.
- `git diff --check`: PASS.

## Consolidation scope

No live Docker, registry, Nexus, Incus or deployment operation was performed.
The historical global evidence file `.codex/evidence/slice-01-distribution.md`
was not modified; Slice 03 evidence remains namespaced below
`.codex/evidence/issue-232/`.
