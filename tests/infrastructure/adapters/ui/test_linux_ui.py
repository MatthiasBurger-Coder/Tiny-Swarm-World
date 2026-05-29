import asyncio
import curses
import unittest
from unittest.mock import patch, MagicMock

from tiny_swarm_world.application.ports.ui.port_ui import (
    AGGREGATE_INSTANCE,
    SETUP_RECOVERY_ACTIONS,
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_FAILED_TO_APPLY,
    STATUS_FAILED_TO_PREPARE,
    STATUS_FAILED_TO_VERIFY,
    STATUS_NOT_RUN,
    STATUS_REFUSED,
    STATUS_RESOURCE_GATED,
    STATUS_SUCCESS,
)
from tiny_swarm_world.infrastructure.adapters.ui.linux_ui import LinuxUI


class TestLinuxUI(unittest.TestCase):
    def setUp(self):
        self.instances = ["Instance1", "Instance2"]
        self.ui = LinuxUI(self.instances)
        self.ui.status = {
            "Instance1": {"current_task": "Starting...", "current_step": "Initializing...", "result": "Pending"},
            "Instance2": {"current_task": "Starting...", "current_step": "Initializing...", "result": "Pending"},
        }

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        asyncio.set_event_loop(None)

    def test_initial_status(self):
        expected_status = {
            "Instance1": {
                "current_task": "Starting...",  # Include the additional field
                "current_step": "Initializing...",
                "result": "Pending",
            },
            "Instance2": {
                "current_task": "Starting...",  # Include the additional field
                "current_step": "Initializing...",
                "result": "Pending",
            },
        }
        self.assertEqual(self.ui.status, expected_status)

    @patch("threading.Lock")
    def test_update_status(self, mock_lock):
        mock_lock_instance = MagicMock()
        mock_lock.return_value = mock_lock_instance
        self.ui.update_status("Instance1", task="", step="Step 1", result="Success")
        self.assertEqual(self.ui.status["Instance1"],
                         {"current_task": "", "current_step": "Step 1", "result": "Success"})

        self.ui.update_status("Instance2", task="", step="Step 2", result="Pending")
        self.assertEqual(self.ui.status["Instance2"]["current_step"], "Step 2")
        self.assertEqual(self.ui.status["Instance2"]["result"], "Pending")

    def test_update_status_records_aggregate_status(self):
        self.ui.update_status(
            AGGREGATE_INSTANCE,
            task="finished",
            step="execution",
            result="Error",
        )

        self.assertEqual(
            {
                "current_task": "finished",
                "current_step": "execution",
                "result": "Error",
            },
            self.ui.aggregate_status,
        )

    def test_terminal_status_contract_accepts_runner_and_executer_values(self):
        terminal_results = (
            "Success",
            "completed",
            "passed",
            "verified",
            "Error",
            "Failed",
            "success",
            "error",
            "failed",
            STATUS_REFUSED,
            STATUS_BLOCKED,
            STATUS_RESOURCE_GATED,
            STATUS_FAILED_TO_PREPARE,
            STATUS_FAILED_TO_APPLY,
            STATUS_FAILED_TO_VERIFY,
            STATUS_NOT_RUN,
            "refused",
            "blocked",
            "resource_gated",
            "resource-gated",
            "failed_to_prepare",
            "failed-to-prepare",
            "failed_to_apply",
            "failed-to-apply",
            "failed_to_verify",
            "failed-to-verify",
            "not_run",
            "not-run",
        )
        for terminal_result in terminal_results:
            with self.subTest(result=terminal_result):
                self.assertTrue(self.ui.is_terminal_result(terminal_result))

        self.assertFalse(self.ui.is_terminal_result("Pending"))

    def test_setup_terminal_states_report_errors_with_recovery_actions(self):
        cases = (
            (STATUS_REFUSED, SETUP_RECOVERY_ACTIONS["refused"]),
            (STATUS_BLOCKED, SETUP_RECOVERY_ACTIONS["blocked"]),
            (STATUS_RESOURCE_GATED, SETUP_RECOVERY_ACTIONS["resource_gated"]),
            (STATUS_FAILED_TO_PREPARE, SETUP_RECOVERY_ACTIONS["failed_to_prepare"]),
            (STATUS_FAILED_TO_APPLY, SETUP_RECOVERY_ACTIONS["failed_to_apply"]),
            (STATUS_FAILED_TO_VERIFY, SETUP_RECOVERY_ACTIONS["failed_to_verify"]),
            (STATUS_FAILED, SETUP_RECOVERY_ACTIONS["failed"]),
            (STATUS_NOT_RUN, SETUP_RECOVERY_ACTIONS["not_run"]),
        )

        for result, expected_recovery in cases:
            with self.subTest(result=result):
                self.ui.update_status("Instance1", task="setup", step="phase", result=result)
                self.ui.update_status("Instance2", task="setup", step="phase", result="Success")

                self.assertTrue(self.ui.all_instances_terminal())
                self.assertEqual("All instances completed with errors", self.ui.completion_summary())
                self.assertEqual(expected_recovery, self.ui.recovery_action(result))

    def test_setup_success_terminal_states_do_not_report_recovery_actions(self):
        for result in (STATUS_SUCCESS, "completed", "passed", "verified"):
            with self.subTest(result=result):
                self.ui.update_status("Instance1", task="setup", step="phase", result=result)
                self.ui.update_status("Instance2", task="setup", step="phase", result=STATUS_SUCCESS)

                self.assertTrue(self.ui.all_instances_terminal())
                self.assertEqual("All instances completed", self.ui.completion_summary())
                self.assertEqual("", self.ui.recovery_action(result))

    def test_success_update_does_not_overwrite_existing_setup_failure_state(self):
        self.ui.update_status("Instance1", task="setup", step="verify", result=STATUS_FAILED_TO_VERIFY)
        self.ui.update_status("Instance1", task="closing", step="Finishing", result=STATUS_SUCCESS)
        self.ui.update_status(
            AGGREGATE_INSTANCE,
            task="finished",
            step="execution",
            result=STATUS_SUCCESS,
        )

        self.assertEqual(STATUS_FAILED_TO_VERIFY, self.ui.status["Instance1"]["result"])
        self.assertEqual("Error", self.ui.aggregate_status["result"])
        self.assertEqual("All instances completed with errors", self.ui.completion_summary())

    def test_recovery_action_normalizes_spacing_and_hyphens(self):
        self.assertEqual(
            SETUP_RECOVERY_ACTIONS["resource_gated"],
            self.ui.recovery_action("resource-gated"),
        )
        self.assertEqual(
            SETUP_RECOVERY_ACTIONS["failed_to_verify"],
            self.ui.recovery_action("failed-to-verify"),
        )

    def test_aggregate_terminal_status_completes_pending_instances(self):
        self.ui.update_status(
            AGGREGATE_INSTANCE,
            task="finished",
            step="execution",
            result="Error",
        )

        self.assertTrue(self.ui.all_instances_terminal())
        self.assertEqual("All instances completed with errors", self.ui.completion_summary())

    @patch("asyncio.get_running_loop", return_value=asyncio.new_event_loop())
    @patch("threading.Thread")
    def test_run_in_thread(self, mock_thread, mock_loop):
        self.ui.start_in_thread()
        mock_thread.assert_called_once()

    @patch("curses.wrapper")
    def test_start_ui(self, mock_wrapper):
        self.ui.start()
        mock_wrapper.assert_called_once_with(self.ui._draw_ui)

    @patch("curses.wrapper")
    def test_start_ui_falls_back_when_curses_is_unavailable(self, mock_wrapper):
        mock_wrapper.side_effect = curses.error("cbreak failed")
        self.ui.test_mode = True

        self.ui.start()

        mock_wrapper.assert_called_once_with(self.ui._draw_ui)

    @patch("curses.wrapper")
    def test_start_ui_terminates_when_all_instances_completed(self, mock_wrapper):
        """New Test: Ensures UI terminates when all instances mark result as completed."""

        def mock_draw_ui(stdscr):
            self.ui.update_status(instance="Instance1", task="", step="Step 1 Complete", result="Success")
            self.ui.update_status(instance="Instance2", task="", step="Step 1 Complete", result="Error")

        mock_wrapper.side_effect = mock_draw_ui

        self.ui.start()

        self.assertEqual(self.ui.status["Instance1"]["result"], "Success")
        self.assertEqual(self.ui.status["Instance2"]["result"], "Error")

    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.curs_set")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.initscr")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.endwin")
    def test_draw_ui_basic_execution(self, mock_endwin, mock_initscr, mock_curs_set):
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_initscr.return_value = mock_stdscr

        # Mock status for the instances
        self.ui.status = {
            "Instance1": {"current_task": "", "current_step": "", "result": ""},
            "Instance2": {"current_task": "", "current_step": "", "result": ""},
        }
        self.ui.lock = MagicMock()
        self.ui.test_mode = True
        # Call the _draw_ui function with the mocked stdscr
        self.ui._draw_ui(mock_stdscr)

        # Verify that curses methods were called
        mock_curs_set.assert_called_once_with(0)
        mock_stdscr.nodelay.assert_called_once_with(True)
        mock_stdscr.timeout.assert_called_once_with(500)

    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.curs_set")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.initscr")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.endwin")
    def test_draw_ui_content_check(self, mock_endwin, mock_initscr, mock_curs_set):
        # Mock for `stdscr`
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)  # Simulate terminal size
        mock_initscr.return_value = mock_stdscr

        # Set instances and statuses
        self.ui.status = {
            "Instance1": {"current_task": "Task1", "current_step": "Downloading", "result": "Success"},
            "Instance2": {"current_task": "Task2", "current_step": "Installing", "result": "In Progress"},
        }

        # Activate test mode
        self.ui.test_mode = True  # Single iteration

        # Call _draw_ui
        self.ui._draw_ui(mock_stdscr)

        # Check for the presence of specific content
        mock_stdscr.addstr.assert_any_call(2, 0, "Task: Task1")  # Content for first instance
        mock_stdscr.addstr.assert_any_call(3, 0, "Step: Downloading")  # Content for first instance
        mock_stdscr.addstr.assert_any_call(4, 0, "Status: Success")  # Status for first instance
        mock_stdscr.addstr.assert_any_call(2, 40, "Task: Task2")  # Content for first instance
        mock_stdscr.addstr.assert_any_call(3, 40, "Step: Installing")  # Content for second instance
        mock_stdscr.addstr.assert_any_call(4, 40, "Status: In Progress")  # Status for second instance

    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.curs_set")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.initscr")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.endwin")
    def test_draw_ui_renders_setup_recovery_action(self, mock_endwin, mock_initscr, mock_curs_set):
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_initscr.return_value = mock_stdscr
        self.ui.status = {
            "Instance1": {"current_task": "setup", "current_step": "preflight", "result": STATUS_REFUSED},
            "Instance2": {"current_task": "setup", "current_step": "not run", "result": "Pending"},
        }
        self.ui.test_mode = True

        self.ui._draw_ui(mock_stdscr)

        calls = [call.args[2] for call in mock_stdscr.addstr.mock_calls]

        self.assertTrue(any("Status: Refused" in call for call in calls))
        self.assertTrue(any("Action: Run with --live" in call for call in calls))

    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.curs_set")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.initscr")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.endwin")
    def test_draw_ui_renders_aggregate_setup_recovery_action(self, mock_endwin, mock_initscr, mock_curs_set):
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_initscr.return_value = mock_stdscr
        self.ui.update_status(AGGREGATE_INSTANCE, task="setup", step="preflight", result=STATUS_BLOCKED)
        self.ui.test_mode = True

        self.ui._draw_ui(mock_stdscr)

        calls = [call.args[2] for call in mock_stdscr.addstr.mock_calls]

        self.assertTrue(any("Overall: Blocked" in call for call in calls))
        self.assertTrue(any("Action: Resolve the reported blocker" in call for call in calls))

    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.curs_set")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.initscr")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.endwin")
    def test_draw_ui_terminates_on_completion(self, mock_endwin, mock_initscr, mock_curs_set):
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_initscr.return_value = mock_stdscr

        # Mock status for the instances, both completing successfully
        self.ui.status = {
            "Instance1": {"current_task": "", "current_step": "Finalizing", "result": "Success"},
            "Instance2": {"current_task": "", "current_step": "Stopping", "result": "Success"},
        }
        self.ui.lock = MagicMock()

        # Call the _draw_ui function with the mocked stdscr
        self.ui._draw_ui(mock_stdscr)

        # Extract all called 3rd arguments (text content)
        calls = [call.args[2] for call in mock_stdscr.addstr.mock_calls]

        # Assert the desired string exists
        assert any("All instances completed" in call for call in calls)

    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.curs_set")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.initscr")
    @patch("tiny_swarm_world.infrastructure.adapters.ui.linux_ui.curses.endwin")
    def test_draw_ui_reports_completion_with_errors(self, mock_endwin, mock_initscr, mock_curs_set):
        mock_stdscr = MagicMock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        mock_initscr.return_value = mock_stdscr
        self.ui.status = {
            "Instance1": {"current_task": "", "current_step": "Finalizing", "result": "Success"},
            "Instance2": {"current_task": "", "current_step": "Stopping", "result": "Failed"},
        }
        self.ui.test_mode = True
        self.ui._draw_ui(mock_stdscr)

        calls = [call.args[2] for call in mock_stdscr.addstr.mock_calls]

        assert any("All instances completed with errors" in call for call in calls)
