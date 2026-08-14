# Developer Manual

This is the implementation entry point. The repository is Python 3.12
automation with hexagonal boundaries; it is not a Java/Spring or React
application.

## Architecture

Start with [arc42](../arc42.adoc), the
[building-block view](../arc42/05_building_blocks.adoc), the
[runtime view](../arc42/06_runtime_view.adoc) and the
[deployment view](../arc42/07_deployment_view.adoc). Domain code stays
independent of application and infrastructure; concrete adapters are wired in
`src/tiny_swarm_world/infrastructure/composition.py`.

## Workflow and changes

Use the [workflow index](../workflow/workflow.index.md),
[issue-completion discipline](../process/issue-completion-discipline.md) and
[branch/CI governance](../governance/branch-protection.md). The repository
[AGENTS.md](../../AGENTS.md) and [QUALITY.md](../../QUALITY.md) are the root
governance authorities. One slice owns one scope and must preserve evidence,
rollback and verification-state semantics.

## Quality

`QUALITY.md` is the quality authority. The standard local command is:

```bash
python3 tools/quality_gate.py quality
```

Run focused tests first, then the required gate. Use WSL/Linux for project
Python and test execution. The [traceability maps](../traceability/) connect
requirements to source, tests and evidence.

## Documentation synchronization

Update the nearest canonical source, relevant arc42/ADR material and audience
manual links when behavior changes. Do not document planned or live behavior
as implemented without evidence.
