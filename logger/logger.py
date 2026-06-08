import logging

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR


def get_logger(logger_name: str, level=DEBUG, log_filename: str = "") -> logging.Logger:
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # File Handler (All levels)
    if log_filename == "":
        log_filename = logger_name + ".log"

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
