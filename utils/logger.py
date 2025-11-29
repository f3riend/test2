from loguru import logger
import os


if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)

logger.add(
    "logs/securebox.log",
    rotation="5 MB",
    level="INFO",
    format="{time} | {level} | {name} | {file}:{line} | {message}",
    mode="w"
)
