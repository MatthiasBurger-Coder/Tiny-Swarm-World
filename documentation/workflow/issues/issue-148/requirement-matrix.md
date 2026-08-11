# Requirement Matrix — Issue #148

Source: [GitHub Issue #148](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/148)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned implementation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-148-01 | Inventory repeated file parsing and subprocess probes in installer bootstrap. | functional | `src/tiny_swarm_world/installer.py` | S148-01 | source inventory | PLANNED |
| REQ-148-02 | Related env-file normalization does not reread the same file repeatedly. | performance | installer env parser | S148-02 | parser tests | PLANNED |
| REQ-148-03 | Preserve export quoting, comments, duplicate detection, empty values, whitespace and malformed-line behavior. | regression | installer parser | S148-02/S148-06 | fixture matrix | PLANNED |
| REQ-148-04 | Git/worktree/ignore probes are reduced or batched without behavior change. | performance | installer metadata probes | S148-03 | mock call-count tests | PLANNED |
| REQ-148-05 | Native group-switch probes are reduced or batched without behavior change. | platform | installer host checks | S148-04 | required/optional probe tests | PLANNED |
| REQ-148-06 | Evidence-context probes are coalesced while keeping deterministic support output. | observability | installer evidence context | S148-05 | evidence snapshot tests | PLANNED |
| REQ-148-07 | Required probe failures remain loud; optional failures degrade to `unknown`. | resilience | probe classification | S148-03/S148-04/S148-05 | failure tests | PLANNED |
| REQ-148-08 | Cache only stable metadata within one installer invocation; never persist host identity/Git/group state across runs. | safety | installer lifecycle | S148-02/S148-05 | scope/static review | PLANNED |
| REQ-148-09 | Bootstrap timing evidence is separate from governed live workflow timing. | performance evidence | shared #152 contract | S148-06 | evidence artifact | PLANNED |
