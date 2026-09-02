# Implementation Summary: #282 / CRED-04

The credential implementation now has one normal path: deterministic
`internal-test` catalog values, explicit operator overrides, and secure-provider
values only in their applicable post-bootstrap lifecycle. The installer no
longer exposes credential-source modes or generates password/recovery state.

Removed behavior includes installer-generated secret files, fixed-secret file
loading, sync-side credential generation/rotation, Infisical bootstrap-file
persistence, the old bootstrap-token environment fallback, and the direct
installer mode flags. The secret manifest now records catalog ownership for
normal managed entries and keeps external user secrets explicit.

The normal wrapper remains thin and delegates file parsing through the
infrastructure composition boundary. Infisical construction is limited to the
service-access profile, uses the validated local endpoint, and is absent from
the default profile. Silent bootstrap retains only protected evidence output;
it does not create a credential-file parent directory.

Documentation, `.env.example`, install-script fixtures, resolver tests,
composition tests, manifest tests, and Infisical client tests were aligned with
the simplified contract.
