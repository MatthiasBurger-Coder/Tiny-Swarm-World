# Native R4 own-transition correction source acceptance

Actual immutable10aa0a57/run67cb1b66d2e148cf98c345d6eb5b6980 stopped the original
three nodes and gracefully shut down LXD, then refused UNIT_STATE_BLOCKED while
systemd still transitioned. Finally recovery saw the same unknown. Explicit
source-bound recovery started the daemon but immediately refused startup
SNAP_WRAPPER_FILE_UNVERIFIED. Later complete original recovering binding passed;
explicit current-state recovery returned RECOVERED and full original preservation.
All three original nodes are Running again; original activation socket remains
inactive. Fixture result is NOT_RUN; no fixture object was created.

Immutable19-file artifact archive SHA2567b6d04f5bd3f0bd49c50ff7d011a70160f3bfeabf0df1326ba04095b2ddb40ff.
Private result ledger49ad3922a15e8b630eb2f0e0e0cb67bc139e08aaaa31ce6e73e930635a87634f
retains each failed phase and the final RECOVERED result. No retrospective PASS.

The correction keeps strict parsers and complete binding, adds only durable
own-transition attribution and bounded UNKNOWN-to-validated observations, with
exact gated ProvenanceError types/codes and no effect in a read window. Root
reviewed the source; independent requirements reviewer verified all three
original candidate pins and found no P1/P2 blocker. Root corrected one test's
expectation of the already-redacting exception constructor and retains a second
unsafe-args test; production source is unchanged from that reviewed candidate.

PC R2 exact-source nearest336 PASS23.275s, logf03ddbd96729dd01f6242b27c2824584cee269e42526ba5bfef40cea56767a2a.
Type974 PASS, loge874ec06b6fdc54ef83f73a8ec3910f9e6d758754cb01e899a15f08e2776e531.
All seven QUALITY PASS;3580 tests/36skips/250.258s,
loga96490404aac220cdc90ad3cd5626af6962ea63c2dccf58f78ed622e38de11b9.
This source gate is not actual live qualification. A new final shared-source
GO/intent and complete native/WSL S02 runs remain required.
