# Physical modules

The repository physically stores implementations and assets under three modules:

```text
modules/
  tsw_core/
    src/tiny_swarm_world/       # domain, application and infrastructure
    src/tsw_core/               # core discovery and packaged descriptor
    infra/config/              # one service catalog and runtime asset tree
    bootstrap/linux/           # shared Linux/WSL preparation, install and CLI
    tools/linux/               # common qualification and developer tooling
  tsw_native_linux/
    install.sh                 # native platform-to-core handoff
    tsw
    module.json
  tsw_windows_wsl/
    bootstrap/windows/         # bootstrap, distro selection, bridge and probes
    tools/windows/
    module.json
```

The Python namespace `tiny_swarm_world`, CLI `tiny-swarm-world`, distribution
name and version 0.2.0 remain unchanged. Root packaging metadata locates actual
Python implementations under `modules/tsw_core/src`; root import shims and
editions are excluded from the wheel. No symlinks or duplicate implementations
supply compatibility.

The deployment root remains the repository/release root. It owns packaging and
lock-file contracts, `.tiny-swarm-world` state, credentials and environment
anchors. `tsw_core.discover_root()` returns that root; its descriptor resolves
physical source/configuration paths beneath it without probing either edition.
Explicit infrastructure overrides retain their original semantics. Historical
release checkouts retain their old source/configuration topology; lifecycle
adapters distinguish those from incomplete physical module deployments. A
missing new core cannot be hidden by legacy directories.

Public `./install.sh`, `./tsw`, documented `bootstrap/linux` commands and public
Windows scripts are thin compatibility forwarders. Native implementation lives
in its module and executes core. Windows runs its physical owner, whose bridge
registration copies the actual bridge implementation and adjacent assets. Its
selected distribution/account handoff invokes physical core preparation then
installation directly. Flags, quoting, stdin, environment and status propagate
through the forwarding entry points. `PYTHONPATH=modules/tsw_core/src` remains an import
compatibility surface; both that path and `PYTHONPATH=modules/tsw_core/src`
load the same physical implementation. Core execution does not need the shims.

The root `host-bindings.json` is compatibility composition data pointing at
Windows-owned physical assets. Core consumes injected host bindings when WSL
integration is requested; it never constructs an edition root. Source proofs
and fingerprints follow physical implementations/configuration and consumed
compatibility entry points. Native edition assets are outside WSL execution
admission; missing, modified or symlinked core/WSL assets remain blockers.

Focused verification on the mandated Windows-host WSL target:

```sh
PYTHONPATH=modules/tsw_core/src python3 -m unittest tests.architecture.test_core_module tests.architecture.test_edition_modules tests.test_install_handoff tests.infrastructure.adapters.lifecycle.test_product_layout
```

Fixtures assert physical ownership and removal of old implementation trees,
core-only deployment without shims/editions, compatibility/direct imports,
public and physical native argv/environment/stdin/status, PowerShell parsing,
public Windows wrappers and selected WSL handoff, package contents and denied
source-integrity paths. These checks do not install or change infrastructure.

The earlier MOD-01/MOD-02–04 delivery isolated ownership in place. That logical
isolation did not satisfy the user's physical restructuring requirement; the
physical correction is tracked separately in the Epic evidence.
