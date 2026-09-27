"""Pure classifiers used at explicit adapter I/O boundaries."""
from __future__ import annotations

import subprocess

import requests

from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure
from tiny_swarm_world.infrastructure.process import (
    ProcessExecutionError, ProcessLaunchError, ProcessTimeoutError,
)


def process_result_failure(
    operation: str, component: str, *, timed_out: bool = False, failure_hint: str | None = None,
) -> OperationFailure:
    cause = "process_timeout" if timed_out else failure_hint or "process_exit_failed"
    if cause not in {"process_timeout", "process_exit_failed", "launch_executable_missing", "launch_permission_denied", "launch_os_error"}:
        cause = "unexpected_failure"
    return OperationFailure.for_cause(operation, component, cause)


def process_failure(error: Exception, operation: str, component: str) -> OperationFailure:
    if isinstance(error, OperationError):
        return error.failure
    if isinstance(error, (ProcessTimeoutError, subprocess.TimeoutExpired, TimeoutError)):
        cause = "process_timeout"
    elif isinstance(error, FileNotFoundError):
        cause = "launch_executable_missing"
    elif isinstance(error, PermissionError):
        cause = "launch_permission_denied"
    elif isinstance(error, (ProcessLaunchError, OSError)):
        cause = "launch_os_error"
    elif isinstance(error, (ProcessExecutionError, subprocess.CalledProcessError)):
        cause = "process_exit_failed"
    else:
        raise TypeError("Only declared process errors can be classified.")
    return OperationFailure.for_cause(operation, component, cause)


def request_failure(error: Exception, operation: str, component: str) -> OperationFailure:
    if isinstance(error, OperationError):
        return error.failure
    if isinstance(error, requests.Timeout):
        cause = "request_timeout"
    elif isinstance(error, requests.ConnectionError):
        cause = "dependency_unavailable"
    elif isinstance(error, requests.RequestException):
        cause = "request_failed"
    else:
        raise TypeError("Only declared request errors can be classified.")
    return OperationFailure.for_cause(operation, component, cause)
