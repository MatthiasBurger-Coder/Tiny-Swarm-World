# Limits and risks

- W03 exposes planning and explicitly approved local manifest metadata persistence, not selective deployment. W04 owns selective setup/preflight/routes/access/verification and CLI live application.
- Minimal plans are not live qualification. Fixed legacy setup still has unconditional artifact/Nexus and routing/Traefik stages; a W03 plan cannot make those stages optional by itself.
- Resource declarations in current native Compose assets are absent; totals are unknown, not host capacity estimates. Capability checking uses supplied capabilities; CLI does not inspect host readiness.
- New desired components have no observed runtime version. Metadata persistence is not service installation or convergence.
- Removal is preview-only, persistent data and deployments are retained. No downgrade, data restore, reset or credential rotation is introduced.
- Fresh selection requires explicit W02 identity/inventory adoption before persistence. Atomic failures retain W02 diagnostics and need inspection/re-preview, not blind retries.
- Local Linux tests are APPLICABLE_LOCAL. Live install/browser checks: NOT_APPLICABLE / LIVE_NOT_APPLICABLE to W03; W09 owns actual native/WSL2 qualification. External quality: EXTERNAL_GATE_NOT_APPLICABLE to this local completion. No live/external success claimed.
