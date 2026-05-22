# Quality Gates

## Minimum Quality Command

From `QUALITY.md`:

```bash
python3 tools/quality_gate.py test
```

## Full Local Quality Gate

From `QUALITY.md`:

```bash
python3 tools/quality_gate.py quality
```

## Documentation And Governance Checks

Use as targeted checks:

```bash
git diff --check
```

Documentation-only checks do not replace the minimum quality command when claiming commit readiness.

## Quality Impact Matrix

| Impact | Typical files | Required gate |
|---|---|---|
| `DOC_ONLY` | Markdown-only documentation with no command, branch, quality, routing, architecture or process-authority change | `git diff --check` plus targeted documentation review |
| `GOVERNANCE_METADATA` | `.agents/**`, `.codex/**`, `documentation/process/**`, `documentation/workflow/**` without product-build impact | `git diff --check` plus targeted registry, routing, structured-format, arc42 or ADR checks |
| `PRODUCT_BUILD_AFFECTING` | product source, tests, build logic, contracts, deployment, runtime wiring or `QUALITY.md` | targeted checks plus the applicable `QUALITY.md` Python gate |
| `UNKNOWN` | unknown or conflicting impact | stop and escalate instead of guessing |

The matrix may reduce unnecessary checks only when the changed file set cannot
influence product build, runtime behavior, contracts, tests, architecture or
quality rules. It must never mark a failed required gate as optional.

## Quality Dimensions

- Build
- Unit Tests
- Integration Tests
- Contract Tests
- Import-linter architecture checks
- Coverage
- Sonar
- Type Checking
- Docker Build
- Security Checks
- Documentation Completeness

## Blocking Rules

- Failed required gates block commit and push.
- Missing required gate evidence blocks commit and push.
- Optional external checks may be documented as skipped only when they are not required by `QUALITY.md`, workflow or CI policy.
- Ad hoc build-tool commands are diagnostic unless `QUALITY.md` defines them as required.

## D8 And Q11 Mapping

`D8` is the blocking quality and release-readiness decision. It includes failed
build, failed tests, architecture violation, missing required documentation,
missing workflow version and failed required quality gates.

`Q11` is asynchronous execution reporting after a successful checkpoint path.
Q11 is non-blocking by default for commit, push, PR creation and release
preparation. Regulatory or compliance reporting blocks only when the active
workflow explicitly declares it as a D8 requirement.
