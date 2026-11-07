# Product Handbook directory migration

The Product Handbook defines the physical documentation layout.
Its [master index](../../README.adoc) and [continuous edition](../../document.adoc)
remain at the documentation root. Each of the seven part directories contains
a `README.adoc` and its canonical specialist sources.

## Source locations

Previous locations in this table describe the layout before this migration.
Use the linked current directories for new references. No compatibility copies
or symlinks are retained at the previous locations.

| Previous repository path | Current source |
| --- | --- |
| `documentation/Howto.adoc` | [documentation/handbook/04-operations/Howto.adoc](../04-operations/Howto.adoc) |
| `documentation/arc42` | [documentation/handbook/02-architecture/arc42](../02-architecture/arc42) |
| `documentation/arc42-template.adoc` | [documentation/handbook/02-architecture/arc42-template.adoc](../02-architecture/arc42-template.adoc) |
| `documentation/arc42.adoc` | [documentation/handbook/02-architecture/arc42.adoc](../02-architecture/arc42.adoc) |
| `documentation/audit` | [documentation/handbook/06-quality-security/audit](../06-quality-security/audit) |
| `documentation/contracts` | [documentation/handbook/01-product/contracts](../01-product/contracts) |
| `documentation/epics` | [documentation/handbook/01-product/epics](../01-product/epics) |
| `documentation/evidence` | [documentation/handbook/07-evidence-release/evidence](../07-evidence-release/evidence) |
| `documentation/governance` | [documentation/handbook/06-quality-security/governance](../06-quality-security/governance) |
| `documentation/manuals/audit-manual.md` | [documentation/handbook/06-quality-security/manuals/audit-manual.md](../06-quality-security/manuals/audit-manual.md) |
| `documentation/manuals/developer-manual.md` | [documentation/handbook/05-development/manuals/developer-manual.md](../05-development/manuals/developer-manual.md) |
| `documentation/manuals/live-validation-manual.md` | [documentation/handbook/07-evidence-release/manuals/live-validation-manual.md](../07-evidence-release/manuals/live-validation-manual.md) |
| `documentation/manuals/operator-manual.md` | [documentation/handbook/04-operations/manuals/operator-manual.md](../04-operations/manuals/operator-manual.md) |
| `documentation/manuals/security-manual.md` | [documentation/handbook/06-quality-security/manuals/security-manual.md](../06-quality-security/manuals/security-manual.md) |
| `documentation/manuals/tools-layout.md` | [documentation/handbook/05-development/manuals/tools-layout.md](../05-development/manuals/tools-layout.md) |
| `documentation/process` | [documentation/handbook/05-development/process](../05-development/process) |
| `documentation/qms` | [documentation/handbook/06-quality-security/qms](../06-quality-security/qms) |
| `documentation/release` | [documentation/handbook/07-evidence-release/release](../07-evidence-release/release) |
| `documentation/reviews` | [documentation/handbook/07-evidence-release/reviews](../07-evidence-release/reviews) |
| `documentation/security` | [documentation/handbook/06-quality-security/security](../06-quality-security/security) |
| `documentation/system` | [documentation/handbook/04-operations/system](../04-operations/system) |
| `documentation/traceability` | [documentation/handbook/07-evidence-release/traceability](../07-evidence-release/traceability) |
| `documentation/user_guide` | [documentation/handbook/03-user-guide/user_guide](../03-user-guide/user_guide) |
| `documentation/workflow` | [documentation/handbook/05-development/workflow](../05-development/workflow) |

The former `documentation/handbook/<part>.adoc` navigation files are now
`documentation/handbook/<part>/README.adoc`.

## Reference and evidence rules

- Maintained links, AsciiDoc includes, CLI help paths, governance references,
  quality-tool inputs and test fixtures use the relocated sources.
- Historical JSON source snapshots and hash manifests retain their recorded
  bytes and paths. Resolve their paths against the recorded revision; they
  do not describe the current checkout.
- Historical `.codex/evidence/` records retain their recorded content.
- Current governing hashes in the skill registry are refreshed for the
  relocated or edited governing sources. Historical hashes are not refreshed.
- New documentation is physically stored below its owning handbook part and
  linked from that part's source catalogue.

## Review scope

Documentation layout and path consumers were reviewed in the main execution
thread using the Documentation Engineer role checklist. No callable subagent
was used. Product behavior, ADR decisions and verification status are unchanged
by the relocation. Publication verification follows the repository's explicit
authorization and SSH/WSL test-host rules. Executed checks and results are
reported in the publication commit and pull request; this migration map does
not establish a test pass or live qualification.
