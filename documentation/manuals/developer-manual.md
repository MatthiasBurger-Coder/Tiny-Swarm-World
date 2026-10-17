# Developer Manual

This is the implementation entry point. The repository is Python 3.12 or newer
automation with hexagonal boundaries; CI tests 3.12, 3.13 and 3.14. It is not
a Java/Spring or React application.

## Architecture

Start with [arc42](../arc42.adoc), the
[building-block view](../arc42/05_building_blocks.adoc), the
[runtime view](../arc42/06_runtime_view.adoc) and the
[deployment view](../arc42/07_deployment_view.adoc). Domain code stays
independent of application and infrastructure; concrete adapters are wired in
`src/tiny_swarm_world/infrastructure/composition.py`.

Read the [resulting architecture and runtime extension guide](../arc42/05_analysis/arch-03-21-resulting-architecture.md)
for package ownership, dependency rules, Classic wiring, fitness functions and
remaining exceptions under [EPIC 03 / #313](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/313).

## Workflow and changes

Use the [workflow documents](../workflow/),
[issue-completion discipline](../process/issue-completion-discipline.md) and
[branch/CI governance](../governance/branch-protection.md). The repository
[AGENTS.md](../../AGENTS.md) and [QUALITY.md](../../QUALITY.md) are the root
governance authorities. One slice owns one scope and must preserve evidence,
rollback and verification-state semantics.

## Local Python environment

Operators use `./prepare_linux.sh` from the trusted checkout, followed by
`./install.sh`. For manual development setup from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --require-hashes -r requirements.lock
python3 -m pip install --no-deps -e .
python3 -m pip install -r requirements-dev.txt
```

The runtime lock is installed before the editable project to avoid a second
runtime dependency resolution. Development dependencies are for local checks.
Run manual tests with `PYTHONPATH=src`; the quality wrapper sets it automatically.
These commands do not prepare Incus or verify installed services.

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
