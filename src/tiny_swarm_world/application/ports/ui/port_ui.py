import asyncio
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

AGGREGATE_INSTANCE = "all"
STATUS_PENDING = "Pending"
STATUS_SUCCESS = "Success"
STATUS_ERROR = "Error"
STATUS_FAILED = "Failed"
STATUS_REFUSED = "Refused"
STATUS_BLOCKED = "Blocked"
STATUS_RESOURCE_GATED = "Resource gated"
STATUS_FAILED_TO_PREPARE = "Failed to prepare"
STATUS_FAILED_TO_APPLY = "Failed to apply"
STATUS_FAILED_TO_VERIFY = "Failed to verify"
STATUS_NOT_RUN = "Not run"
SUCCESS_RESULTS = frozenset({"success", "completed", "passed", "verified"})
SETUP_RECOVERY_ACTIONS = {
    "blocked": "Resolve the reported blocker and rerun setup.",
    "failed": "Inspect the failed phase evidence before retrying.",
    "failed_to_apply": "Repair the apply failure before rerunning setup.",
    "failed_to_prepare": "Repair the preparation failure before rerunning setup.",
    "failed_to_verify": "Repair the verification failure before rerunning setup.",
    "not_run": "Resolve the earlier stopped phase before this phase can run.",
    "refused": "Provide --live and the required live consent before retrying.",
    "resource_gated": "Use a host that satisfies the resource contract or select a smaller profile.",
}
FAILURE_RESULTS = frozenset(
    {
        "error",
        "failed",
        "refused",
        "blocked",
        "resource_gated",
        "failed_to_prepare",
        "failed_to_apply",
        "failed_to_verify",
        "not_run",
    }
)
TERMINAL_RESULTS = SUCCESS_RESULTS | FAILURE_RESULTS


class PortUI(ABC):
    def __init__(self, instances, test_mode=False):
        self.instances = instances
        self.status = {
            instance: {
                "current_task": "Starting...",
                "current_step": "Initializing...",
                "result": STATUS_PENDING,
            }
            for instance in instances
        }
        self.aggregate_status = {
            "current_task": "Starting...",
            "current_step": "Initializing...",
            "result": STATUS_PENDING,
        }
        self.lock = threading.Lock()
        self.ui_thread = None
        self.test_mode = test_mode

    def update_status(self, instance, task, step, result=None):
        with self.lock:
            target_status = self._status_for_instance(instance)
            if target_status is not None:
                target_status["current_task"] = task
                target_status["current_step"] = step
                if result is not None:
                    target_status["result"] = self._safe_result_update(instance, result)

    def _status_for_instance(self, instance):
        if instance == AGGREGATE_INSTANCE:
            return self.aggregate_status
        return self.status.get(instance)

    def all_instances_terminal(self):
        if self.is_terminal_result(self.aggregate_status["result"]):
            return True
        return all(
            self.is_terminal_result(self.status[instance]["result"])
            for instance in self.instances
        )

    def is_terminal_result(self, result):
        return _normalize_result(result) in TERMINAL_RESULTS

    def is_failure_result(self, result):
        return _normalize_result(result) in FAILURE_RESULTS

    def is_success_result(self, result):
        return _normalize_result(result) in SUCCESS_RESULTS

    def has_failure_result(self):
        aggregate_result = self.aggregate_status["result"]
        return self.is_failure_result(aggregate_result) or any(
            self.is_failure_result(self.status[instance]["result"])
            for instance in self.instances
        )

    def completion_summary(self):
        if self.has_failure_result():
            return "All instances completed with errors"
        return "All instances completed"

    def recovery_action(self, result):
        return SETUP_RECOVERY_ACTIONS.get(_normalize_result(result), "")

    def _safe_result_update(self, instance, result):
        if not self.is_success_result(result):
            return result
        if instance == AGGREGATE_INSTANCE and self.has_failure_result():
            return STATUS_ERROR

        target_status = self._status_for_instance(instance)
        if target_status is not None and self.is_failure_result(target_status["result"]):
            return target_status["result"]
        return result

    def start_in_thread(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        executor = ThreadPoolExecutor(max_workers=1)
        self.ui_thread = loop.run_in_executor(executor, self.start)

    @abstractmethod
    def start(self):
        pass


def _normalize_result(result) -> str:
    return str(result).strip().lower().replace(" ", "_").replace("-", "_")
