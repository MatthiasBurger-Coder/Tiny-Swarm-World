
import time
import curses
from tiny_swarm_world.application.ports.ui.port_ui import PortUI

class LinuxUI(PortUI):
    def __init__(self, instances, test_mode=False):
        """test_mode: If True, the UI will exit after 2 seconds."""
        super().__init__(instances, test_mode)

    def update_status(self, instance, task, step, result=None):
        """
        Updates the status of an instance.
        """
        super().update_status(instance, task, step, result)

    def _draw_ui(self, stdscr):
        """
        Draws the UI using curses.
        """
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)
        stdscr.timeout(500)

        previous_status = {instance: {"current_task": "", "current_step": "", "result": ""} for instance in
                           self.instances}

        while True:
            height, width = stdscr.getmaxyx()

            # Limiting the column width between 20 and 50 characters
            col_width = max(20, min(width // len(self.instances), 50))

            stdscr.clear()

            # Check if the terminal is large enough
            if height < max(len(self.instances) + 8, 8):
                stdscr.addstr(0, 0, f"Terminal too small ({height}x{width})!".center(width), curses.A_BOLD)
                stdscr.refresh()
                time.sleep(3)
                return

            # Print headers
            for idx, instance in enumerate(self.instances):
                stdscr.addstr(0, idx * col_width, instance.center(col_width), curses.A_BOLD)

            changed = False
            with self.lock:
                for idx, instance in enumerate(self.instances):
                    current_task = self.status[instance]["current_task"]
                    current_step = self.status[instance]["current_step"]
                    current_result = self.status[instance]["result"]

                    if (previous_status[instance]["current_step"] != current_step or
                            previous_status[instance]["result"] != current_result or
                            previous_status[instance]["current_task"] != current_task):
                        changed = True
                        previous_status[instance]["current_task"] = current_task
                        previous_status[instance]["current_step"] = current_step
                        previous_status[instance]["result"] = current_result

                    # Ensure content does not exceed column width
                    stdscr.addstr(2, idx * col_width, f"Task: {current_task[:col_width - 7]}")
                    stdscr.addstr(3, idx * col_width, f"Step: {current_step[:col_width - 7]}")
                    stdscr.addstr(4, idx * col_width, f"Status: {current_result[:col_width - 7]}")
                    recovery_action = self.recovery_action(current_result)
                    if recovery_action:
                        stdscr.addstr(5, idx * col_width, f"Action: {recovery_action[:col_width - 8]}")

                aggregate_result = self.aggregate_status["result"]
                if self.is_terminal_result(aggregate_result):
                    stdscr.addstr(6, 0, f"Overall: {aggregate_result}"[:width], curses.A_BOLD)
                    aggregate_recovery = self.recovery_action(aggregate_result)
                    if aggregate_recovery:
                        stdscr.addstr(7, 0, f"Action: {aggregate_recovery}"[:width])

            if changed:
                stdscr.refresh()

            time.sleep(0.5)

            # Handle completion of all instances
            if self.all_instances_terminal():
                completion_summary = self.completion_summary()
                # Ensure "All instances completed" fits within the terminal
                summary_row = len(self.instances) + 7
                if summary_row < height:
                    stdscr.addstr(summary_row, 0, completion_summary.center(width)[:width],
                                  curses.A_BOLD)
                else:
                    # Print in the last line if there's no space
                    stdscr.addstr(height - 1, 0, completion_summary.center(width)[:width], curses.A_BOLD)

                stdscr.refresh()
                if not self.test_mode:
                    time.sleep(2)
                    break

            if self.test_mode:
                break

    def start(self):
        """
        Runs the curses-based UI.
        """
        try:
            curses.wrapper(self._draw_ui)
        except curses.error:
            self._wait_without_curses()

    def _wait_without_curses(self):
        while not self.test_mode and not self.all_instances_terminal():
            time.sleep(0.2)
