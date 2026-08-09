# Requirement Matrix — Issue #153

Source: [GitHub Issue #153](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/153)

Status at workflow authoring: `PLANNED`.

| ID | Requirement | Type | Planned documentation area | Slice | Verification/evidence | Status |
|---|---|---|---|---|---|---|
| REQ-153-01 | User-facing docs state that LXD/Incus is a hard prerequisite for default `lxc_native`. | documentation | `documentation/user-handbook.adoc`, installation guide/README as needed | S153-02 | doc scan/review | PLANNED |
| REQ-153-02 | Docs state Tiny Swarm World does not install or initialize LXD/Incus automatically. | documentation | user-facing installation docs | S153-02 | doc scan | PLANNED |
| REQ-153-03 | Docs state `lxc`/`incus` commands must work without sudo from the same shell as `./install.sh`. | documentation | prerequisite section/checklist | S153-02/S153-03 | doc review | PLANNED |
| REQ-153-04 | A ready-for-install checklist exists. | documentation | handbook/installation guide | S153-03 | checklist review | PLANNED |
| REQ-153-05 | A minimal LXD/Incus smoke test exists. | documentation/verification | handbook/troubleshooting/installation guide | S153-03 | static command validation; live optional state | PLANNED |
| REQ-153-06 | Host Docker versus Docker inside LXC/Incus nodes is distinguished. | documentation | architecture/install docs | S153-04 | doc review | PLANNED |
| REQ-153-07 | Installation order is documented from host preparation through service deployment. | documentation | installation guide | S153-04 | sequence review | PLANNED |
| REQ-153-08 | Common failure cases and user actions are documented. | documentation | troubleshooting/handbook | S153-05 | failure-case checklist | PLANNED |
| REQ-153-09 | Existing documentation is updated instead of unnecessary duplication. | documentation governance | existing docs inventory | S153-01/S153-06 | duplicate/overlap review | PLANNED |
| REQ-153-10 | No source behavior changes unless strictly required by a verified contradiction. | non-goal | no `src/` change by default | S153-01/S153-07 | changed-files audit | PLANNED |

