import platform

from tiny_swarm_world.application.ports.ui.port_ui import PortUI
from tiny_swarm_world.infrastructure.os_types import OsTypes



class FactoryUI:

    def __init__(self):
        self.os_type = OsTypes.get_enum_from_value(platform.system())

    def get_ui(self, **kwargs) -> PortUI:
        if self.os_type == OsTypes.WINDOWS:
            from tiny_swarm_world.infrastructure.adapters.ui.windows_ui import WindowsUi
            return WindowsUi(**kwargs)
        else :
            from tiny_swarm_world.infrastructure.adapters.ui.linux_ui import LinuxUI
            return LinuxUI(**kwargs)