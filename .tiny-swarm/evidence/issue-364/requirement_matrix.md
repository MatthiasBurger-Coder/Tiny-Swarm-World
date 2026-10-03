# Issue #364 requirement matrix

Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/364 (complete issue read 2026-10-03). Parent: #313.

Documentation-only scope; no product, workflow, ADR decision or live infrastructure change. Branch: `docs/arch-03-21-resulting-architecture`.

| ID | Requirement from issue | Type | Files likely affected | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|---|---|
| R364-01 | Document package responsibilities and explicit dependency/ownership rules | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | ownership table; layer graph | source inspection; architecture gates | VERIFIED — independent audit PASS |
| R364-02 | Describe ports/adapters, runtime boundary and composition root | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | Classic port-to-adapter wiring | source inspection; runtime/composition tests | VERIFIED — independent audit PASS |
| R364-03 | Explain orchestration flow and planning versus execution | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | flow and additive planner caveat | source inspection; lifecycle/planner tests | VERIFIED — independent audit PASS |
| R364-04 | Explain configuration, secret and process boundaries | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | boundary contracts and safe diagnostics | source inspection; architecture/process checks | VERIFIED — independent audit PASS |
| R364-05 | Document architecture fitness functions | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | gate-to-rule table | executed gates; QUALITY.md comparison | VERIFIED — independent audit PASS |
| R364-06 | Provide step-by-step runtime extension path using Classic | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | extension guide, contract limits and unsupported future runtimes | source comparison; Classic regressions | VERIFIED — independent audit PASS |
| R364-07 | Record remaining exceptions/debt rather than hiding them | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | owned debt table with follow-ups | allowlist, cycle and planner inspection | VERIFIED — independent audit PASS |
| R364-08 | Link documentation from parent #313 and developer guides | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | navigation links and parent issue reference | local link validation; parent issue readback | VERIFIED — independent audit PASS |
| R364-09 | Ensure documentation matches implemented code | Documentation | arc42 resulting-architecture guide; arc42 views; developer manual; README; parent issue | source-linked implemented/planned distinctions | independent completion review | VERIFIED — independent audit PASS |

Preflight: clean working tree on main; task branch created before writes. Active workflow is completed issue #355 on another branch; it is preserved and is not executed or regenerated. No issue-364 slice or competing live agent lock exists in this session. Writes are limited to documentation navigation, the new architecture guide and issue evidence. No new architecture decision is proposed. Verification found the README governing hash cache needed refreshing; scope includes that single JSON hash field, reviewed under skill-registry-conflict-auditor with registry checks.

Final artifacts: [guide](../../../documentation/arc42/05_analysis/arch-03-21-resulting-architecture.md), [test results](test_results.md), [independent audit](completion_audit.md), [final report](final_report.md). All nine rows passed independent completion review.
