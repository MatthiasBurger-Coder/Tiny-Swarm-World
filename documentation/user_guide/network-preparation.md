# Kernel and browser-access preparation

Run preparation from an ordinary account in the supported Ubuntu Linux/WSL
checkout. Keep package, Incus and network consent separate:

```bash
./prepare_linux.sh --dry-run
./prepare_linux.sh
./prepare_linux.sh --preflight
```

Read-only modes never create host/configuration/state/evidence files or start a
stopped daemon. Apply shows the exact pending stage and asks for consent. Rerun
after any required logout/login; a declined or interrupted stage is not ready.
Preparation does not deploy nodes or services, or authorize an installation reset.

Network planning consumes the canonical provider bridges, ports and local route
names. It activates only the three declared forwarding/bridge sysctls, prepares
owned persistence, scopes IPv4 forwarding to the managed bridge/subnet and current
default egress, and maintains a delimited Linux hosts block. Existing Incus NAT
remains Incus-owned. Names resolve locally before service deployment, so resolution
alone does not establish service availability.

The supported firewall path uses iptables-nft, recognizes Incus rules and retains
active UFW ownership. UFW additions use its scoped route/DHCP/DNS interfaces.
Preparation does not install or enable UFW. A missing UFW executable is accepted
only when complete inventory shows no residual UFW configuration or ownership.
Unknown firewall owners, contradictory deny rules, incompatible IPv6 bridges,
missing Incus NAT, port/subnet collisions, unsafe files or conflicting outside
hosts entries block before the network stage changes the host. Preserve the
reported resource, review the owner/configuration diagnostic and rerun dry-run.
Never disable or flush the firewall to bypass a blocker.

Byte-compatible safe persistence files are reused without writes. An incompatible
existing file is preserved; its filename alone does not authorize replacement.
Linux hosts changes retain unrelated entries and metadata with a protected backup.
Failures stop dependent actions and record confirmed/uncertain effects. Inspect
the printed protected evidence, then obtain a fresh plan and new consent before
resuming. No automatic rollback removes another application's resources.

For Windows browser access, use the selected distribution with the existing
Windows preparation and bridge owner. Windows operations require an elevated
session of the Windows account that owns that distribution; Linux `sudo` does
not grant Windows administrator rights. Standalone Windows preparation retains
the W04 candidate qualification and exact target/source/plan consent guards; see
[Windows preparation](windows-preparation.md). Linux preparation separately binds
its approved source, target and network plan when delegating to the same bridge.
The bridge stores its protected
bundle/configuration/registration and remains the sole owner of Windows hosts,
portproxy and firewall rules. A new registration opens the existing credential
dialog for the Windows account that owns the WSL distribution. An owned matching
registration reuses its credentials. Account mismatch or foreign ownership blocks.

Preparation separates Linux kernel/forwarding/name prerequisites, Windows routing
configuration/agent readiness, deployed endpoint/API reachability and actual login.
Bridge readiness may succeed before services are deployed. API reachability does
not prove authentication. `services_verified` remains false during preparation.
The existing Windows service agent reconciles changed WSL addresses after restart;
W06 adds no second updater or scheduled task.

Local mocked tests verify the preparation contract. Live installation, restart,
browser and login qualification require separately authorized recoverable-host
execution with exact committed revision, versions, commands, exit codes and
redacted evidence. Current local development grants no live host mutation consent.
