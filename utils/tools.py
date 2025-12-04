from rich.progress import Progress, TextColumn, TimeElapsedColumn, ProgressColumn
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from rich.console import Console
from rich.text import Text
from .logger import auto_logger
import subprocess
import platform
import hashlib
import base64
import json
import time
import os


logger = auto_logger()

class ASCIIBar(ProgressColumn):
    """Straight forward ascii progress bar"""
    def render(self, task):
        bar_width = 30
        progress = task.percentage / 100
        done = int(bar_width * progress)
        remaining = bar_width - done

        bar = "[" + "=" * done + ">" + " " * (remaining - 1) + "]"
        return Text(bar)


def protect_file(path):
    if platform.system() in ["Linux", "Darwin"]:
        try:
            subprocess.run(["chattr", "+i", path], check=True)
            logger.info(f"{path} is now in an unchangeable/unmodifiable state.")
        except Exception as e:
            logger.warning("File protection error:", e)
    
    if platform.system() == "Windows":
        try:
            os.system(f'icacls "{path}" /deny %USERNAME%:D')
            logger.info(f"{path} now permanently deleted (Windows).")
        except Exception as e:
            logger.warning("File protection error:", e)


