# Shared core module

`tsw_core` isolates ownership in place. The existing `tiny-swarm-world` 0.2.0
distribution, `tiny_swarm_world` Python namespace and CLI entry point remain
unchanged. `src/tsw_core/module.json` declares the core source, configuration,
shared Linux bootstrap and runtime metadata roots. `tsw_core.discover_root` and
`resource_root` govern default infrastructure discovery. Both packaging
entry points explicitly include only the core namespaces and package the
descriptor. This keeps edition packages outside the core build boundary.

The core owns all existing domain, application and infrastructure layers,
Linux-side preparation and lifecycle workflows, and the single `infra/config`
service catalog, compose tree and runtime helpers. Existing paths stay stable;
no compatibility symlinks bypass prerequisite or source-identity checks.

Native Linux and Windows/WSL entry-point separation remains in #505 and #506.
The existing `tsw` and `install.sh` entry points continue invoking the core.
The repository-level `host-bindings.json` supplies Windows-owned bridge asset
paths as compatibility composition outside core ownership. An edition entry
point can supply `TSW_HOST_BINDINGS_PATH`. The existing script/config path
overrides remain supported. Core adapters resolve the supplied binding only
when Windows integration is requested; native core discovery and CLI loading
need neither binding nor edition assets. WSL preparation still requires and
hashes its host assets, including the binding, before mutation. Missing host
assets fail closed. Core code never assumes a Windows bootstrap directory.

The wheel retains the existing Python-runtime packaging scope and adds the
core descriptor. Deployment still supplies the existing shared bootstrap and
configuration trees; they are not newly embedded into the Python wheel.
The module split introduces no release pipeline or product version change.

Focused verification covers core-only imports/CLI loading, resource discovery,
Python layer and module dependencies, external binding/source fingerprints,
and offline wheel contents. #503 excludes full suites and live installation,
update, recovery and infrastructure mutation from this work.
