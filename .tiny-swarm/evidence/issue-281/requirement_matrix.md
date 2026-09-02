# Requirement Matrix: #281 / CRED-03

| ID | Requirement | Scope | Implementation target | Verification | Status |
|---|---|---|---|---|---|
| CRED-03-REQ-001 | One precedence rule is implemented centrally and documented. | functional | `domain/configuration/credential_resolution.py`, application service, precedence documentation | resolver tests; documentation review | VERIFIED |
| CRED-03-REQ-002 | Bootstrap resolution never queries self-hosted Infisical for its own startup inputs. | security / lifecycle | bootstrap phase rejects self-hosted secure lookup; bootstrap sequence supplies operator/default inputs | `test_self_hosted_infisical_is_rejected_during_bootstrap`; sequence documentation | VERIFIED |
| CRED-03-REQ-003 | Explicit operator values override deterministic defaults. | functional | central resolver and simple/legacy installer integration | operator/default precedence tests | VERIFIED |
| CRED-03-REQ-004 | Applicable secure/Infisical values override operator/default values only in an available lifecycle phase. | functional / lifecycle | post-bootstrap secure source input and source metadata | vault precedence and post-bootstrap sync tests | VERIFIED |
| CRED-03-REQ-005 | Source metadata reports only `default`, `operator`, or `vault`. | observability | redaction-safe snapshots, sync results, and installer context | metadata decoding/context tests; secret scan | VERIFIED |
| CRED-03-REQ-006 | External Infisical is either genuinely supported or explicitly rejected when mixed with self-hosted bootstrap. | architecture / safety | external provider mode is explicitly rejected; self-hosted URL is local-only | provider conflict tests; setup documentation | VERIFIED |
| CRED-03-REQ-007 | Unsupported/conflicting override combinations fail with actionable, non-secret errors. | safety | resolver, secure-file, provider, and bootstrap override validation | invalid metadata/path/provider/override tests | VERIFIED |
| CRED-03-REQ-008 | Legacy generated/fixed/infisical modes are inventoried and mapped to the new lifecycle; deletion remains CRED-04. | compatibility | explicit legacy mapping and compatibility boundary documentation | documentation review; legacy mode tests remain green | VERIFIED |
| CRED-03-REQ-009 | Infisical synchronization is not required to obtain self-hosted bootstrap inputs. | lifecycle | bootstrap resolution precedes independent post-bootstrap synchronization | composition and sync-order tests; sequence documentation | VERIFIED |
| CRED-03-REQ-010 | Tests cover no override, operator override, vault override, self-hosted bootstrap, external/conflict behavior, and reruns. | quality | domain/application/adapter/installer regression suite | focused suite: 154 tests, OK | VERIFIED |
| CRED-03-REQ-011 | Introduced or materially changed code reaches at least 95% branch-aware coverage. | quality-gate | all changed production paths including compatibility routing | diff-added-line branch-aware report: 100% (all measured changed lines) | VERIFIED |

## Verification applicability

The default authority for CRED-03 is local verification. No live Infisical,
Docker, Incus, Swarm, or network action is authorized by this issue. Live
installation evidence remains deferred to #285 / CRED-07.

## Redaction boundary

Evidence may include credential key names, lifecycle phase, source label, and
status. It must not include credential values, tokens, authorization headers,
raw environment files, or private endpoints.
