import asyncio
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor


class PortUI(ABC):
    def __init__(self, instances, test_mode=False):
        self.instances = instances
        self.status = {
            instance: {
                "current_task": "Starting...",
                "current_step": "Initializing...",
                "result": "Pending",
            }
            for instance in instances
        }
        self.lock = threading.Lock()
        self.ui_thread = None
        self.test_mode = test_mode

    def update_status(self, instance, task, step, result=None):
        with self.lock:
            if instance in self.status:
                self.status[instance]["current_task"] = task
                self.status[instance]["current_step"] = step
                if result:
                    self.status[instance]["result"] = result

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
