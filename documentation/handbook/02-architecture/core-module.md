# Physical modules

The repository stores implementations and assets under two modules:

```text
modules/
  tsw_core/
    src/                       # domain, application and infrastructure
    src/module.json            # packaged core descriptor
    infra/config/              # service catalog and runtime assets
    tools/linux/               # shared quality and developer tools
    tests/                     # shared runtime and architecture tests
  tsw_native_linux/
    boostrap/                  # Linux preparation, install and CLI
    tools/                     # compatibility tool forwarders
    install.sh                 # native platform-to-core handoff
    tsw
    module.json
    tests/
```

Root packaging maps `tiny_swarm_world` to `modules/tsw_core/src` and `tsw_core`
to `modules/tsw_core`. The Python namespace, CLI `tiny-swarm-world`, distribution
name and version 0.2.0 remain unchanged. Root import shims are excluded from
the wheel; they load the same physical implementation.

The deployment root owns packaging and lock-file contracts, local state and
credential/environment anchors. `tsw_core.discover_root()` returns that root;
the core descriptor resolves physical source/configuration paths beneath it.
Explicit infrastructure overrides retain their semantics. Lifecycle adapters
recognize historical release layouts and reject incomplete module deployments.

Public `./install.sh` and `./tsw` are thin forwarders to the Linux module,
which invokes core. Flags, quoting, stdin, environment and status propagate
through the forwarding entry points.

Windows preparation and bridge assets have been removed. Core retains legacy host models and adapters, but standard host preparation
registers only the native Linux adapter. This checkout supplies no Windows
bridge implementation or root host-binding configuration. A required
missing external binding remains a blocker; Linux installation needs no such
binding. Historical Windows delivery records do not describe current assets.

When verification is authorized, module ownership and native forwarding are
covered by `modules.tsw_core.tests.architecture.test_core_module`,
`modules.tsw_core.tests.architecture.test_edition_modules` and
`modules.tsw_core.tests.infrastructure.adapters.lifecycle.test_product_layout`.
Follow `AGENTS.md` for the required remote test target.
