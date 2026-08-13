# Issue #125 Remaining Risks

1. The contract cannot prove runtime behavior until a consented run supplies
   redacted evidence for A/B/C on the applicable host classes.
2. Operator secret, CA, DNS and resource prerequisites remain external inputs.
3. A future run must keep failed, partial and resource-gated states rather than
   collapsing them into one result.
4. External SonarQube status remains unavailable until the actual system result
   can be observed.
