# Acceptance Checklist — #348 / ARCH-03.05

- [x] One canonical `RuntimeProfileResolver` owns profile/backend resolution.
- [x] Typed inputs include user/provider intent, service profile, host platform, and available capabilities.
- [x] Composition backend selection delegates to the resolver instead of duplicating candidate branching.
- [x] Equivalent inputs resolve deterministically.
- [x] Classic Docker Swarm/Incus selection behavior remains covered by existing composition tests.
- [x] Supported and unsupported resolution cases have focused tests.
- [x] Local quality gate passed; no live infrastructure command was run.
