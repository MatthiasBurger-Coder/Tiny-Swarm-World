from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.stack_asset_transfer import (
    StackAssetTransfer,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


class TestStackAssetTransfer(unittest.TestCase):
    def test_service_access_asset_uses_generated_dashboard(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            transfer = StackAssetTransfer(
                project_paths=ProjectPaths.from_roots(Path(temporary_directory)),
                run_manager_shell=Mock(),
                render_service_access_dashboard=lambda: "<html>generated</html>",
            )

            transfer.transfer_stack_assets("service-access", "/remote/service-access")

        transfer._run_manager_shell.assert_called_once_with(
            "set -e; mkdir -p /remote/service-access/dashboard; "
            "cat > /remote/service-access/dashboard/index.html",
            input_text="<html>generated</html>",
        )

    def test_unknown_stack_has_no_asset_side_effect(self):
        run_manager_shell = Mock()
        transfer = StackAssetTransfer(
            project_paths=ProjectPaths.from_roots(Path("/tmp/project")),
            run_manager_shell=run_manager_shell,
            render_service_access_dashboard=Mock(),
        )

        transfer.transfer_stack_assets("unknown", "/remote/unknown")

        run_manager_shell.assert_not_called()
