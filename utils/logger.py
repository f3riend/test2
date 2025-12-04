# logs.py
from loguru import logger
import os
import inspect

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def auto_logger():
    """
    Automatically creates a separate log file for the module from which
    this function is called.

    Example:
        module1.py  -> logs/module1.log
        main.py     -> logs/main.log
    """


    frame = inspect.stack()[1]
    file_path = frame.filename


    filename = os.path.splitext(os.path.basename(file_path))[0]

    log_file = f"{LOG_DIR}/{filename}.log"


    for handler in logger._core.handlers.values():
        if hasattr(handler._sink, "name") and handler._sink.name == log_file:
            return logger

    logger.add(
        log_file,
        rotation="5 MB",
        level="INFO",
        format="{time} | {level} | {name} | {file}:{line} | {message}",
        encoding="utf-8",
        mode="w"
    )

    return logger
