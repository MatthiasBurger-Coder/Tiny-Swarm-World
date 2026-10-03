"""Installation sequencing, independent of host, process, storage and terminal technology."""

from __future__ import annotations
from collections.abc import Mapping
from pathlib import Path
from tiny_swarm_world.application.ports.installation import (
    InstallerOptions,
    InstallerPaths,
    InstallerSecretEntry,
    HostRuntime,
    InstallReporter,
    InstallerError,
    _InstallRunContext,
    HostPreparation,
    ConfigurationPreparation,
    CredentialsPreparation,
    PhaseRunner,
    InstallationEvidence,
    InstallationPresentation,
)


class InstallationService:
    def __init__(
        self,
        host: HostPreparation,
        configuration: ConfigurationPreparation,
        credentials: CredentialsPreparation,
        process: PhaseRunner,
        evidence: InstallationEvidence,
        presentation: InstallationPresentation,
    ) -> None:
        self.host = host
        self.configuration = configuration
        self.credentials = credentials
        self.process = process
        self.evidence = evidence
        self.presentation = presentation
        self.phases = InstallationPhases(host, process, evidence, presentation)
        self.run_evidence = InstallationRunEvidence(evidence, presentation)

    def run(
        self,
        options: InstallerOptions,
        *,
        env: Mapping[str, str],
        cwd: Path,
        reporter: InstallReporter | None = None,
    ) -> int:
        install_reporter = reporter or self.presentation.reporter()
        self.host.require_repository(cwd)
        host_runtime = self.host.detect(env)
        if options.native_reconcile:
            if host_runtime.name != "native_linux":
                raise InstallerError(
                    "Native reconciliation requires a native Linux host."
                )
            self.host.validate_native(options, env, cwd)
            self.configuration.validate_read_only(options, env, cwd, host_runtime)
            if options.preflight_only or options.dry_run:
                self.presentation.message(
                    "Native host, configuration, credentials and setup preflight passed without mutation."
                )
                if options.dry_run:
                    self.presentation.message(
                        "Dry run plan: validate configuration and credentials; reconcile the "
                        f"{options.service_profile} profile; verify deployment health; "
                        "print access targets. Managed state will not be reset."
                    )
                return 0
        elif options.preflight_only or options.dry_run:
            raise InstallerError(
                "Installer --preflight and --dry-run require native Linux."
            )
        paths = self.configuration.paths(env, cwd)
        self.host.authorize(
            host_runtime,
            cwd,
            allow_wsl_windows_filesystem=options.allow_wsl_windows_filesystem,
            env=env,
        )
        python_bin = (
            self.process.current_python()
            if options.native_reconcile
            else self.process.ensure_python(host_runtime, paths, env)
        )
        with self.configuration.snapshot(
            options, env, cwd, host_runtime
        ) as prepared_env:
            return self._run_prepared(
                options,
                prepared_env,
                cwd,
                install_reporter,
                self.configuration.paths(prepared_env, cwd),
                host_runtime,
                python_bin,
            )

    def _run_prepared(
        self,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        install_reporter: InstallReporter,
        paths: InstallerPaths,
        host_runtime: HostRuntime,
        python_bin: str,
    ) -> int:
        install_env, required_entries = self.credentials.prepare(options, env, paths)

        evidence_dir, approval_argument = self.run_evidence.create(
            options, install_env, cwd, paths, host_runtime, required_entries
        )

        self.presentation.plan(
            cwd,
            options,
            evidence_dir,
        )
        install_reporter.report(
            self.presentation.event(
                "INSTALL_STARTED",
                "RUNNING",
                "install",
                message=(
                    f"Mode: {'native-reconcile' if options.native_reconcile else 'fresh-reset'}; Profile: {options.service_profile}; "
                    f"Provider: {install_env.get('TSW_NODE_PROVIDER', 'lxc_native')}"
                ),
            )
        )
        if options.native_reconcile and options.confirm_reset:
            raise InstallerError(
                "Native install does not reset; use a separately confirmed platform reset."
            )
        if not options.native_reconcile:
            self.presentation.confirm_reset(options)
        if not options.headless and not self.process.recorder_available():
            raise InstallerError(
                "Required command 'script' is not available for terminal recording. Use --headless to capture logs directly."
            )
        self.evidence.append(
            evidence_dir,
            {
                "reset_confirmation_present": "no"
                if options.native_reconcile
                else "yes",
                "reset_confirmation_source": "not_applicable"
                if options.native_reconcile
                else (
                    "explicit_flag" if options.confirm_reset else "interactive_prompt"
                ),
            },
        )

        if not self.phases._check_bridge(
            host_runtime, install_env, cwd, install_reporter, evidence_dir
        ):
            return 1

        reset_command = self.process.command(
            python_bin, "reset", options, approval_argument
        )
        setup_command = self.process.command(
            python_bin, "setup", options, approval_argument
        )

        if options.native_reconcile:
            self.evidence.append(
                evidence_dir, {"reset_skipped_for_native_reconcile": "yes"}
            )
        else:
            reset_exit = self.phases._run_reset(
                options, install_env, cwd, install_reporter, evidence_dir, reset_command
            )
            if reset_exit != 0:
                return reset_exit

        return self.phases._run_setup(
            options, install_env, cwd, install_reporter, evidence_dir, setup_command
        )


class InstallationPhases:
    """Phase policy keeps reset and setup exits and evidence ordering explicit."""

    def __init__(
        self,
        host: HostPreparation,
        process: PhaseRunner,
        evidence: InstallationEvidence,
        presentation: InstallationPresentation,
    ) -> None:
        self.host = host
        self.process = process
        self.evidence = evidence
        self.presentation = presentation

    def _check_bridge(
        self,
        host_runtime: HostRuntime,
        install_env: Mapping[str, str],
        cwd: Path,
        install_reporter: InstallReporter,
        evidence_dir: Path,
    ) -> bool:
        bridge_guard = self.host.bridge(host_runtime, install_env, cwd)
        self.evidence.append(
            evidence_dir,
            self.evidence.bridge_context(bridge_guard),
        )
        if not bridge_guard.passed:
            install_reporter.report(
                self.presentation.event(
                    "INSTALL_FINISHED",
                    "FAILED",
                    "windows-wsl-bridge",
                    reason="Windows <-> WSL bridge is not prepared.",
                    evidence_path=evidence_dir,
                    suggested_commands=self.presentation.bridge_commands(
                        bridge_guard.reason
                    ),
                )
            )
            self.presentation.bridge_failure(bridge_guard, evidence_dir)
            self.evidence.append(
                evidence_dir,
                {
                    "reset_skipped_due_to_windows_wsl_bridge": "yes",
                    "setup_skipped_due_to_windows_wsl_bridge": "yes",
                    "finished_utc": self.evidence.timestamp(),
                },
            )
            return False

        return True

    def _run_reset(
        self,
        options: InstallerOptions,
        install_env: Mapping[str, str],
        cwd: Path,
        install_reporter: InstallReporter,
        evidence_dir: Path,
        reset_command: str,
    ) -> int:
        reset_exit = self.process.phase(
            "fresh-install reset",
            reset_command,
            self.evidence.path(evidence_dir, "reset-run.log"),
            options,
            install_env,
            cwd,
            install_reporter,
            sequence=1,
            total=2,
        )
        self.evidence.write(
            self.evidence.path(evidence_dir, "reset-run.exit"), f"{reset_exit}\n"
        )
        self.evidence.append(evidence_dir, {"reset_exit": str(reset_exit)})
        if reset_exit != 0:
            install_reporter.report(
                self.presentation.event(
                    "INSTALL_FINISHED",
                    "FAILED",
                    "install",
                    reason="Fresh-install reset failed. Setup was not started.",
                    evidence_path=evidence_dir,
                )
            )
            self.presentation.message(
                f"Fresh-install reset failed with exit code {reset_exit}. Setup will not start.",
                failed=True,
            )
            self.presentation.message(
                f"Evidence directory: {evidence_dir}", failed=True
            )
            self.evidence.append(
                evidence_dir,
                {
                    "setup_skipped_due_to_reset_failure": "yes",
                    "finished_utc": self.evidence.timestamp(),
                },
            )
            self.presentation.tail(
                self.evidence.path(evidence_dir, "reset-run.log"),
                "Last reset log lines",
            )
            self.presentation.reset_guidance(
                self.evidence.path(evidence_dir, "reset-run.log")
            )
            return reset_exit

        return reset_exit

    def _run_setup(
        self,
        options: InstallerOptions,
        install_env: Mapping[str, str],
        cwd: Path,
        install_reporter: InstallReporter,
        evidence_dir: Path,
        setup_command: str,
    ) -> int:
        setup_exit = self.process.phase(
            "live setup",
            setup_command,
            self.evidence.path(evidence_dir, "setup-run.log"),
            options,
            install_env,
            cwd,
            install_reporter,
            sequence=1 if options.native_reconcile else 2,
            total=1 if options.native_reconcile else 2,
        )
        self.evidence.write(
            self.evidence.path(evidence_dir, "setup-run.exit"), f"{setup_exit}\n"
        )
        self.evidence.append(
            evidence_dir,
            {
                "setup_exit": str(setup_exit),
                "finished_utc": self.evidence.timestamp(),
            },
        )
        if setup_exit == 0:
            install_reporter.report(
                self.presentation.event(
                    "INSTALL_FINISHED",
                    "SUCCEEDED",
                    "install",
                    message="Installation completed successfully.",
                    evidence_path=evidence_dir,
                )
            )
            self.presentation.completion(0, evidence_dir, failed=False)
        else:
            install_reporter.report(
                self.presentation.event(
                    "INSTALL_FINISHED",
                    "FAILED",
                    "install",
                    reason=f"Live setup failed with exit code {setup_exit}.",
                    evidence_path=evidence_dir,
                )
            )
            self.presentation.completion(setup_exit, evidence_dir, failed=True)
            self.presentation.tail(
                self.evidence.path(evidence_dir, "setup-run.log"), "Last log lines"
            )
            self.presentation.setup_guidance(
                self.evidence.path(evidence_dir, "setup-run.log")
            )
        return setup_exit


class InstallationRunEvidence:
    """Build installation provenance before executing managed-state phases."""

    def __init__(
        self, evidence: InstallationEvidence, presentation: InstallationPresentation
    ) -> None:
        self.evidence = evidence
        self.presentation = presentation

    def create(
        self,
        options: InstallerOptions,
        install_env: Mapping[str, str],
        cwd: Path,
        paths: InstallerPaths,
        host_runtime: HostRuntime,
        required_entries: tuple[InstallerSecretEntry, ...],
    ) -> tuple[Path, str]:
        git_probe = self.evidence.git_probe(cwd, ".tiny-swarm-world/")
        if git_probe.inside_worktree and not git_probe.path_ignored:
            self.presentation.message(
                "WARN: .tiny-swarm-world/ is not ignored by git; do not commit local evidence or credential overrides.",
                failed=True,
            )

        run_id = self.evidence.run_id()
        try:
            evidence_dir = self.evidence.directory(
                install_env,
                cwd=cwd,
                host_runtime=host_runtime,
                run_id=run_id,
            )
        except (OSError, RuntimeError) as error:
            raise InstallerError(
                "Secure installation evidence directory is unavailable; ensure its operator-owned parent directories are mode 0700."
            ) from error
        live_mode, approval_source, approval_argument = self.presentation.approval(
            options
        )
        terminal_mode = "headless" if options.headless else "terminal_recorder"
        evidence_probes = self.evidence.probes(cwd, git_probe)
        self.evidence.write_context(
            evidence_dir,
            context=_InstallRunContext(
                run_id=run_id,
                service_profile=options.service_profile,
                secret_env_file=paths.secret_env_file,
                checked_secret_keys=tuple(entry.key for entry in required_entries),
                host_runtime=host_runtime,
                live_execution_mode=live_mode,
                live_approval_source=approval_source,
                terminal_recording_mode=terminal_mode,
                cwd=cwd,
                env=install_env,
                git_probe=git_probe,
                evidence_probes=evidence_probes,
                native_reconcile=options.native_reconcile,
            ),
        )

        return evidence_dir, approval_argument
