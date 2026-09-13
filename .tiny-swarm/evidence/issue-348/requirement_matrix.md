# Requirement Matrix — #348 / ARCH-03.05

Parent: #313 — EPIC 03

| ID | Requirement from issue | Type | Implementation evidence | Verification evidence | Status |
|---|---|---|---|---|---|
| REQ-001 | Runtime/profile selection has one canonical owner. | architecture | `RuntimeProfileResolver` owns normalization and provider/backend resolution; composition delegates compatibility lookup to it. | Resolver unit tests and architecture/type checks. | DONE |
| REQ-002 | Inputs include user intent, validated configuration, detected platform, and available runtime capabilities. | architecture / functional | Typed `RuntimeProfileResolutionRequest` carries service profile, provider request, host environment, and available backends. | Request/model tests covering deterministic input mapping. | DONE |
| REQ-003 | Application workflows do not duplicate profile-resolution branching. | architecture | Existing composition backend selection delegates to the resolver; workflow services receive resolved/typed inputs without new branching. | Composition regression tests and architecture gate. | DONE |
| REQ-004 | Resolution is deterministic for equivalent inputs. | functional / quality | Pure resolver uses ordered candidates and explicit preferred-backend rules. | Repeated/equivalent input resolver tests. | DONE |
| REQ-005 | Classic Docker Swarm behavior remains unchanged. | compatibility | Existing supported provider/backend selection and composition compatibility helpers remain intact. | Existing platform/composition tests and full quality gate. | DONE |
| REQ-006 | Supported and unsupported resolution cases are covered by tests. | quality | Resolver tests cover supported, unsupported provider, unsupported preferred backend, and unavailable candidates. | Focused resolver test suite. | DONE |
