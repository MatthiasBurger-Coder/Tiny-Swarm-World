# EPIC #452 bootstrap completion architecture plan

Status: PLANNED / UNQUALIFIED. Workflow authoring only, 2026-10-17.

The [active workflow](../../workflow/workflow.md) maps all W01–W10 delivery to remaining original EPIC obligations. The [W10 audit](../../evidence/issue-462-bootstrap-completion-audit.md) remains INCOMPLETE; historical W09 amended existing-host results do not qualify clean hosts or ordinary Windows Apply.

Current owners remain application preparation/installation ports and services, concrete Linux/Windows adapters, infrastructure composition and the existing canonical Windows bridge. Ordinary native/WSL installation reconciles; explicit destructive reset remains separate under the accepted W07 ADR. Docker/Swarm remain within Incus-managed nodes. No new runtime or orchestrator is proposed.

Remaining transitions require S452-01 accepted architecture/security decisions: equivalent credential/evidence protection for trusted archives without Git; independently verified local source delivery to the ordinary Linux account before Python; evidence-bound Windows release admission with explicit invalidation/requalification rules. New policy must not bypass Git-ignore/source/ownership/qualification guards. These are planned, not implemented or approved by this analysis.

Runtime sequence: trusted release -> read-only plan -> separate consented preparation stages -> any operator account/restart/session boundary -> reinventory -> explicit installation -> service/route/browser verification. READY proves preparation only. Product Python runs solely on Linux/WSL. Preparation consent does not approve installation/reset, persist across drift or authorize live qualification.

S02–04 repair demonstrated gaps through existing owners; S05 freezes a committed candidate and complete scenario matrix; S06/07 qualify recoverable clean targets only with explicit consent; S08 implements reviewed admission; S09 witnesses final ordinary paths at final source; S10 updates current documentation and independently audits completion. Any behavior-affecting admission change requires affected scenarios to rerun. An exact-SHA evidence/admission identity contract must prevent circular self-qualification.

Deployment view (`../07_deployment_view.adoc`) and risks (`../11_risks_and_debt.adoc`) were checked for Incus ownership, privilege boundaries, resource feasibility and evidence limits. They remain unchanged pending verified implementation. Risks include archive secret exposure, source transfer collision/tampering, Windows reserve starvation, global WSL disruption, partial nontransactional package changes and false parent qualification. Mitigations are accepted policy before code, explicit scoped consent, preserved configuration/resources, bounded commands, protected checkpoints and source-bound qualification.

Rollback is slice-aware code reversion after dependency review. APT/features and account changes are nontransactional; no whole-host or external-volume recovery guarantee is introduced. Independent completion auditing requires every original requirement and scenario; unverified items remain OPEN/BLOCKED.
