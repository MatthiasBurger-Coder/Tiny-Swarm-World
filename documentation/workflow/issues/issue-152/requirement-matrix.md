# Requirement Matrix — Issue #152

Source: [GitHub Issue #152](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/152)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-152-01 | A documented performance evidence contract exists. | governance | performance evidence documentation | S152-01/S152-05 | contract review | PLANNED |
| REQ-152-02 | Issues #144–#148 can use one evidence location and schema. | traceability | shared evidence path/schema | S152-02/S152-04 | cross-workflow contract checks | PLANNED |
| REQ-152-03 | Schema records workflow/issue ID, segment, environment summary, timestamps or duration, counters, baseline/new values and limitations. | observability | typed value object/schema | S152-02 | serialization tests | PLANNED |
| REQ-152-04 | A small helper or clear template records measurements without heavyweight benchmarking. | functional | helper/adapter/template | S152-03 | helper tests and diff review | PLANNED |
| REQ-152-05 | Contract supports single-computer and future multi-node/worker flows. | scalability | schema dimensions | S152-02/S152-03 | fixture coverage | PLANNED |
| REQ-152-06 | Measurements do not require external services and state environment limitations. | safety/evidence | docs and local writer | S152-03/S152-05 | static documentation check | PLANNED |
| REQ-152-07 | Tests cover stable serialization/template rendering and missing optional values. | quality gate | unit tests | S152-05 | targeted unittest | PLANNED |
| REQ-152-08 | Documentation explains baseline/new comparison without treating local timing as globally absolute. | documentation | performance evidence guide | S152-05 | doc review | PLANNED |
| REQ-152-09 | The issue does not implement the #144–#148 optimizations itself. | non-goal | workflow scope | S152-01/S152-06 | changed-files audit | PLANNED |

