import logging
from pathlib import Path

from tiny_swarm_world.infrastructure.project_paths import logs_root

class LoggerFactory:
    """
    A central logger factory class for logging within the application.
    This class ensures that loggers are instance-bound and do not have duplicate FileHandlers.
    It can be used in any other class via dependency injection.
    """

    @staticmethod
    def get_logger(cls, log_dir: str | Path | None = None, level: int = logging.INFO):
        """
        Creates or returns a logger for the given class.

        :param cls: The class reference or class name as a string.
        :param log_dir: Directory for log file_management.
        :param level: Logging level.
        :return: Configured logger.
        """
        log_path = Path(log_dir) if log_dir is not None else logs_root()
        class_name = cls.__name__ if isinstance(cls, type) else str(cls)
        log_file = log_path / f"{class_name}.log"

        # Ensure the log directory exists
        log_path.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(class_name)
        logger.setLevel(level)

        # Remove duplicate FileHandlers
        if logger.hasHandlers():
            for handler in logger.handlers[:]:  # Copy the list to iterate safely
                if isinstance(handler, logging.FileHandler):
                    logger.removeHandler(handler)
                    handler.close()

        # Add file handler if none exists
        file_handler = logging.FileHandler(log_file, mode="a")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger
