from infrastructure.logging.logger_factory import LoggerFactory


class SocatManager:
    def __init__(self):
        self.logger = LoggerFactory.get_logger(self.__class__)

    def set_service_socat_ports(self):
        pass
