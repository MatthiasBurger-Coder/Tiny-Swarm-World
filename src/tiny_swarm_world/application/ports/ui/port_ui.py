import asyncio
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

AGGREGATE_INSTANCE = "all"
STATUS_PENDING = "Pending"
STATUS_SUCCESS = "Success"
STATUS_ERROR = "Error"
STATUS_FAILED = "Failed"
TERMINAL_RESULTS = frozenset(
    {
        STATUS_SUCCESS,
        STATUS_ERROR,
        STATUS_FAILED,
        "success",
        "error",
        "failed",
    }
)
FAILURE_RESULTS = frozenset({STATUS_ERROR, STATUS_FAILED, "error", "failed"})


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
                if result:
                    target_status["result"] = result

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
        return str(result) in TERMINAL_RESULTS

    def has_failure_result(self):
        aggregate_result = self.aggregate_status["result"]
        return str(aggregate_result) in FAILURE_RESULTS or any(
            str(self.status[instance]["result"]) in FAILURE_RESULTS
            for instance in self.instances
        )

    def completion_summary(self):
        if self.has_failure_result():
            return "All instances completed with errors"
        return "All instances completed"

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
