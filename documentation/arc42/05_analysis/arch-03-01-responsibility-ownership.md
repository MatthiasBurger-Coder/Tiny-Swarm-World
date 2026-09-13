# ARCH-03.01 — Responsibility Ownership and Migration Map

The table assigns a future owner before any code is moved. It is the review
contract for ARC-02 through ARC-06 and keeps migration decisions tied to actual
responsibilities.

| Responsibility | Current location | Required classification | Intended owner | Migration slice | Guardrail |
|---|---|---|---|---|---|
| CLI argument parsing and workflow registry | `__main__.py:135-317` | `ENTRYPOINT` / `PRESENTATION` | CLI parser and workflow registry adapter | ARC-02 | Existing workflow names and exit behavior remain regression-covered. |
| Consent and confirmation interaction | `__main__.py:546-579`, `839-849` | `PRESENTATION` with application policy input | CLI consent adapter plus application request | ARC-02 | Preserve explicit live-consent and destructive confirmation semantics. |
| CLI workflow dispatch | `__main__.py:582-719` | `APPLICATION_ORCHESTRATION` at the edge | CLI dispatcher calling application services | ARC-02 | No concrete adapter construction outside composition. |
| CLI result rendering | `__main__.py:721-879`, `965-1097` | `PRESENTATION` | CLI renderer | ARC-02 | Keep JSON/text output and status/exit mapping equivalent. |
| Installer phase sequencing | `installer.py:284-500` | `APPLICATION_ORCHESTRATION` | Installer application service | ARC-03 | Preserve reset/setup order, failure propagation, and evidence generation. |
| Installer process execution | `installer.py:917-943`, `1164-1210`, `1609-1640` | `INFRASTRUCTURE_ADAPTER` | Process/command runner adapter | ARC-03 | Preserve timeout, termination, output capture, and redaction behavior. |
| Host/runtime and filesystem assessment | `installer.py:504-816` | `DOMAIN_POLICY` plus `INFRASTRUCTURE_ADAPTER` | Domain assessment plus host/filesystem adapters | ARC-03 | Preserve Linux/WSL behavior and Windows-mounted filesystem safety rules. |
| Installer evidence and logs | `installer.py:515-550`, `1054-1163`, `1289-1365` | `INFRASTRUCTURE_ADAPTER` | Evidence/log repository and reporter | ARC-03 | Evidence paths and safe metadata remain deterministic. |
| Installer presentation and failure guidance | `installer.py:1020-1044`, `1070-1159`, `1413-1591` | `PRESENTATION` | Installer renderer/reporter | ARC-03 | No credential or raw secret leakage; preserve actionable failure states. |
| Simple bootstrap credential loading | `simple_installer.py:86-216` | `INFRASTRUCTURE_ADAPTER` / `LEGACY_COMPATIBILITY` | Credential/configuration adapter | ARC-03 | Keep ownership/mode checks and precedence semantics. |
| Operator access summary | `simple_installer.py:218-235` | `PRESENTATION` | Installer CLI renderer | ARC-03 | Continue suppressing password values. |
| Concrete adapter binding | `infrastructure/composition_runtime.py` and focused modules | `COMPOSITION` | Capability-specific composition modules | ARC-04 | Composition remains the only normal binding location. |
| Compatibility facade and patch points | `infrastructure/composition.py` | `COMPOSITION` / `LEGACY_COMPATIBILITY` | Composition facade owner | ARC-04/06 | Keep compatibility imports working until consumers migrate; do not grow the facade surface. |
| Domain rules and typed policies | `src/tiny_swarm_world/domain/**` | `DOMAIN_POLICY` | Domain | Preserve | No application/infrastructure imports. |
| Use-case orchestration and ports | `src/tiny_swarm_world/application/**` | `APPLICATION_ORCHESTRATION` | Application | Preserve | No concrete infrastructure imports. |

## Migration ordering

1. ARC-05 should add root-boundary guardrails from this baseline before moving
   behavior.
2. ARC-02 should isolate CLI parsing, dispatch, and rendering while preserving
   workflow and consent contracts.
3. ARC-03 should establish one installer lifecycle owner and extract process,
   filesystem, host, evidence, and presentation boundaries incrementally.
4. ARC-04 should untangle composition capability dependencies and remove the
   cycle without breaking the public facade.
5. ARC-06 should reduce and govern the remaining compatibility exception set.

The audit does not prescribe a generic framework, a maximum file size, or a
pattern hierarchy. A migration is justified only when it removes one of the
documented dependency or responsibility findings.
