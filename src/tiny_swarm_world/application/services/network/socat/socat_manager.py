import logging


class SocatManager:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_service_socat_ports(self):
        # Reserved extension point; socat port wiring is intentionally disabled.
        pass
