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

The three ownership descriptors live under `src/tsw_core`,
`src/tsw_native_linux` and `src/tsw_windows_wsl`. Edition directories contain
ownership metadata, not separately released Python distributions. Edition assets
remain isolated in place, preserving public paths and source-identity guards.
Only the core namespaces enter the existing Python distribution.

`tsw_native_linux` owns the public `./install.sh` and `./tsw` entry points.
They forward arguments, environment, stdin and process status to the single
shared implementations at `bootstrap/linux/install.sh` and
`bootstrap/linux/run.sh`. Native-host orchestration and Linux prerequisites
remain core behavior, as they are also used inside WSL.

`tsw_windows_wsl` owns `bootstrap/windows`, `tools/windows` and
`host-bindings.json`: bootstrap, distribution selection, bridge, Linux guest
probes and source proof. Its existing `prepare_windows.ps1` entry point retains
flags and status handling. The selected distribution/account handoff invokes
`bootstrap/linux/prepare_linux.sh` followed by `bootstrap/linux/install.sh`
directly, without the native edition entry points. The read-only handoff proof
requires and hashes the core installer at its new path. Its executable source
surface excludes native entry points and their ownership descriptor; the core
and WSL source, configuration, tools and bridge assets retain integrity checks.
Windows Git admission and the offline proof builder exclude only the native
entry points and ownership directory from their clean-source check; core or WSL
edits still block admission. No edition imports or executes the other; the core
imports neither.
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

The focused separation checks are:

```sh
PYTHONPATH=src python3 -m unittest tests.architecture.test_core_module tests.architecture.test_edition_modules tests.test_install_handoff
```

Run on the repository-mandated WSL test host. The edition test invokes a
PowerShell parser and public Windows entry point with a stub preparation module,
then exercises selected distro/user arguments and failed WSL results with a stub
process port. It never launches a distribution. Native fixtures contain only the
public launchers, core shell scripts and a stub Python executable. Negative
fixtures detect forbidden dependency edges/imports and missing shared assets.
