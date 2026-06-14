import curses
import time

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
        self._configure_screen(stdscr)
        previous_status = self._initial_previous_status()

        while True:
            height, width, col_width = self._screen_dimensions(stdscr)
            stdscr.clear()

            if self._terminal_too_small(stdscr, height, width):
                return

            self._draw_headers(stdscr, col_width)
            changed = self._draw_status_columns(stdscr, col_width, previous_status)
            self._draw_aggregate_status(stdscr, width)

            if changed:
                stdscr.refresh()

            time.sleep(0.5)

            if self._draw_completion_if_terminal(stdscr, height, width):
                break

            if self.test_mode:
                break

    def _configure_screen(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(500)

    def _initial_previous_status(self):
        return {
            instance: {"current_task": "", "current_step": "", "result": ""}
            for instance in self.instances
        }

    def _screen_dimensions(self, stdscr):
        height, width = stdscr.getmaxyx()
        instance_count = max(len(self.instances), 1)
        col_width = max(20, min(width // instance_count, 50))
        return height, width, col_width

    def _terminal_too_small(self, stdscr, height, width):
        if height >= max(len(self.instances) + 8, 8):
            return False
        stdscr.addstr(0, 0, f"Terminal too small ({height}x{width})!".center(width), curses.A_BOLD)
        stdscr.refresh()
        time.sleep(3)
        return True

    def _draw_headers(self, stdscr, col_width):
        for idx, instance in enumerate(self.instances):
            stdscr.addstr(0, idx * col_width, instance.center(col_width), curses.A_BOLD)

    def _draw_status_columns(self, stdscr, col_width, previous_status):
        changed = False
        with self.lock:
            for idx, instance in enumerate(self.instances):
                current_status = self.status[instance]
                if self._status_changed(previous_status[instance], current_status):
                    changed = True
                    previous_status[instance].update(current_status)
                self._draw_instance_status(stdscr, idx, col_width, current_status)
        return changed

    def _status_changed(self, previous_status, current_status):
        return (
            previous_status["current_step"] != current_status["current_step"]
            or previous_status["result"] != current_status["result"]
            or previous_status["current_task"] != current_status["current_task"]
        )

    def _draw_instance_status(self, stdscr, idx, col_width, current_status):
        column = idx * col_width
        current_task = current_status["current_task"]
        current_step = current_status["current_step"]
        current_result = current_status["result"]
        stdscr.addstr(2, column, f"Task: {current_task[:col_width - 7]}")
        stdscr.addstr(3, column, f"Step: {current_step[:col_width - 7]}")
        stdscr.addstr(4, column, f"Status: {current_result[:col_width - 7]}")
        recovery_action = self.status_recovery_action(current_status)
        if recovery_action:
            stdscr.addstr(5, column, f"Action: {recovery_action[:col_width - 8]}")
        evidence_path = current_status.get("evidence_path", "")
        if evidence_path:
            stdscr.addstr(6, column, f"Evidence: {evidence_path[:col_width - 10]}")
        correlation_id = current_status.get("correlation_id", "")
        if correlation_id:
            stdscr.addstr(7, column, f"Trace: {correlation_id[:col_width - 7]}")

    def _draw_aggregate_status(self, stdscr, width):
        aggregate_result = self.aggregate_status["result"]
        if not self.is_terminal_result(aggregate_result):
            return
        stdscr.addstr(6, 0, f"Overall: {aggregate_result}"[:width], curses.A_BOLD)
        aggregate_recovery = self.status_recovery_action(self.aggregate_status)
        if aggregate_recovery:
            stdscr.addstr(7, 0, f"Action: {aggregate_recovery}"[:width])
        evidence_path = self.aggregate_status.get("evidence_path", "")
        if evidence_path:
            stdscr.addstr(8, 0, f"Evidence: {evidence_path}"[:width])

    def _draw_completion_if_terminal(self, stdscr, height, width):
        if not self.all_instances_terminal():
            return False
        completion_summary = self.completion_summary()
        summary_row = min(len(self.instances) + 7, height - 1)
        stdscr.addstr(summary_row, 0, completion_summary.center(width)[:width], curses.A_BOLD)
        stdscr.refresh()
        if self.test_mode:
            return False
        time.sleep(2)
        return True

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
