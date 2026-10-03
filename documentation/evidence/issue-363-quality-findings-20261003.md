# Issue 363: follow-up for two local quality findings

Scope: the operator explicitly requested fixes for the stale README governing
hash and the Pester launcher failure from a Linux-native WSL checkout.
The broader lifecycle and RC1 requirements of issue 363 remain outside this
follow-up; successful installation evidence is unchanged.

The skill registry now records the actual README SHA256. No README content or
other governing hash changed. The existing integrity test verifies the cache.

The legacy bridge test keeps direct mounted-drive execution and uses bounded
`wslpath -w` conversion for native WSL paths. Windows treats WSL UNC scripts as
remote under RemoteSigned, so the launcher copies the exact five required test
and bridge assets into a uniquely named Windows temporary directory, preserving
their relative layout. Pester executes the copied scripts and cleans up in
`finally`. No execution policy or service configuration changes. Windows output
and Python decoding use UTF-8. Converter failures fail explicitly; failed or
empty Pester runs return nonzero. Existing availability skips are unchanged.

Verification and independent completion review are recorded in
`.tiny-swarm/evidence/issue-363-quality-findings/`. Protected raw logs are under
`/home/micro/.local/state/tiny-swarm-world/evidence/issue-363-quality-findings/`.
