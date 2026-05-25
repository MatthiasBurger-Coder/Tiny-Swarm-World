# Architecture Baseline

## Checked Sources

- `AGENTS.md`
- `QUALITY.md`
- `documentation/epics/autonomous-runnable-setup.md`
- `documentation/epics/system-unification.md`
- `documentation/architecture/adr-autonomous-setup-safety.adoc`
- `documentation/arc42/02_constraints.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`
- `tests/architecture/test_hexagonal_imports.py`
- `.importlinter`

## Baseline Findings

- Current governance and documentation still identify Multipass as the primary
  platform provider.
- The accepted setup safety contract is provider-shaped but names Multipass in
  several concrete readiness and mutation examples.
- Architecture tests allow existing Platform application service directories
  including `multipass`, `network`, `vm`, `setup`, and `platform`.
- New provider orchestration should stay inside existing Platform boundaries
  unless architecture tests and docs are deliberately updated.
- Domain and application import constraints remain valid and must not be
  weakened for LXD/Incus work.

## Architecture Direction

- Introduce provider-neutral domain and application port contracts.
- Add LXD/Incus as infrastructure adapters.
- Keep raw LXC low-level commands out of the first implementation.
- Keep Multipass as explicit legacy/fallback.
- Keep live provider probes non-mutating until operator-approved live phases.

## arc42 Status

arc42 was checked during workflow creation. No arc42 files were changed during
workflow authoring. Slice 01 and Slice 10 must update arc42 after the provider
decision and implementation are made.
