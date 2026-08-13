# Issue #125 Requirement Matrix

This issue defines a future evidence contract. It does not execute or claim a
live run. Contract requirements are `VERIFIED_LOCAL` when the document exists
and is internally consistent; future runtime states remain `PLANNED` or
`LIVE_CONSENT_MISSING`.

| ID | Requirement | Implementation | Check/evidence | Status |
|---|---|---|---|---|
| REQ-125-01 | Create canonical live-greenpath contract | `documentation/evidence/live-greenpath-evidence-contract.md` | file/content review | VERIFIED_LOCAL |
| REQ-125-02 | Create reusable live-run template | `documentation/evidence/live-run-template.md` | field review | VERIFIED_LOCAL |
| REQ-125-03 | Create redaction rules | `documentation/evidence/redaction-rules.md` | sensitive-field review | VERIFIED_LOCAL |
| REQ-125-04 | Create live smoke checklist | `documentation/evidence/live-smoke-checklist.md` | category review | VERIFIED_LOCAL |
| REQ-125-05 | Represent explicit operator consent | template host/consent fields; verification policy | state review | VERIFIED_LOCAL |
| REQ-125-06 | Cover native Linux and WSL2 | scenario/host matrix | field review | VERIFIED_LOCAL |
| REQ-125-07 | Cover fresh install, reconcile/re-run and update | A/B/C scenario matrix | field review | VERIFIED_LOCAL |
| REQ-125-08 | Cover preflight through nodes, Docker, Swarm and network | phase contract/checklist | category review | VERIFIED_LOCAL |
| REQ-125-09 | Cover Traefik/TLS/DNS/browser/admin evidence | contract and smoke checklist | field review | VERIFIED_LOCAL |
| REQ-125-10 | Cover secrets without values | contract and redaction rules | sensitive-field review | VERIFIED_LOCAL |
| REQ-125-11 | Cover Nexus/artifacts and service readiness | phase contract/checklist | category review | VERIFIED_LOCAL |
| REQ-125-12 | Cover Jenkins, SonarQube, Pulsar and Swagger | phase/checklist categories | category review | VERIFIED_LOCAL |
| REQ-125-13 | Cover Service Access | contract/checklist | category review | VERIFIED_LOCAL |
| REQ-125-14 | Define phase result and retry semantics | template phases, attempts and policy states | field/state review | VERIFIED_LOCAL |
| REQ-125-15 | Define blocked/refused/resource/failure states | verification policy references | exact state review | VERIFIED_LOCAL |
| REQ-125-16 | Define checksum manifest | SHA-256 contract and template | field/review procedure | VERIFIED_LOCAL |
| REQ-125-17 | Define independent review | template review fields and closeout | field review | VERIFIED_LOCAL |
| REQ-125-18 | Define cleanup, rollback and dependent-phase stop | contract/checklist | resilience review | VERIFIED_LOCAL |
| REQ-125-19 | Prevent raw secrets, tokens, env and command dumps | redaction rules | content review | VERIFIED_LOCAL |
| REQ-125-20 | Keep future live success distinct from contract existence | explicit `PLANNED` wording and policy states | status review | VERIFIED_LOCAL |
| REQ-125-21 | Handoff to #124 traceability and Green-Path | links and scenario fields | path review | VERIFIED_LOCAL |
| REQ-125-22 | No live commands or local evidence capture in this issue | workflow scope and current-state text | workflow review | VERIFIED_LOCAL |

Future scenario execution remains `LIVE_CONSENT_MISSING` until an approved
operator run produces redacted evidence for the actual target.
