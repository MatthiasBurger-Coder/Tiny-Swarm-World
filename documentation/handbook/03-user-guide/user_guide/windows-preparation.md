# Windows preparation tooling removed

Windows preparation and bridge tooling are no longer shipped in this checkout.
The former Windows setup entry point has also been removed.

Use the [Linux installation instructions](installation.adoc) from a prepared
Linux environment. This does not provide Windows feature activation, WSL
lifecycle management, Windows certificate trust or Windows browser forwarding.
Existing WSL runtime adapters still require any applicable external-host bindings;
missing prerequisites remain blockers.

Earlier Windows preparation instructions and qualification results are historical
and remain available in Git and the [evidence catalogue](../../07-evidence-release/README.adoc).
They do not qualify this checkout or restore the removed tools.
