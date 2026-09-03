# Implementation Summary: #284 / CRED-06

CRED-06 aligns the normal installer experience and user-facing documentation
with the simplified CRED-01 through CRED-04 contract. `./install.sh` remains
the Linux/WSL entry point and delegates to `simple_installer`, which resolves
the internal-test catalog without a credential-preparation ceremony.

After a successful run, the installer prints actionable Portainer and
Infisical URLs plus login identifiers and the catalog reference. It never
prints password values or derived secret material. `.env.example` now presents
empty optional override entries, so copying it does not imply that credentials
must be supplied manually.

The installation guide, handbook, RC1 bootstrap contract, troubleshooting
guide, runtime architecture, and installer debugger now use the canonical
entry point and describe the same catalog/override/Infisical model. The docs
make the internal development/test boundary explicit: AD/LDAP/SSO, VPN,
firewall, network segmentation, and IAM remain enterprise responsibilities.
Stale mode, generated-password, and credential-recovery preparation guidance
was removed or changed to explicit negative statements.
