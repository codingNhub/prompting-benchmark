# Configures three loggers: experiment, errors, debug. Call get_logger(name) in any module.# Configures three loggers: experiment, errors, debug. Call get_logger(name) in any module.

import logging
import os


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # Prevent adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create logs folder if it does not exist
    os.makedirs("logs", exist_ok=True)

    # Format for all log entries
    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)

    # experiment.log — INFO and above — normal run records
    exp_handler = logging.FileHandler("logs/experiment.log", encoding="utf-8")
    exp_handler.setLevel(logging.INFO)
    exp_handler.setFormatter(formatter)

    # errors.log — ERROR and above — anything that went wrong
    err_handler = logging.FileHandler("logs/errors.log", encoding="utf-8")
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)

    # Console — INFO — so you can watch experiments run in terminal
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    logger.addHandler(exp_handler)
    logger.addHandler(err_handler)
    logger.addHandler(console)

    return logger