from rich.progress import Progress, TextColumn, TimeElapsedColumn, ProgressColumn
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from rich.console import Console
from rich.text import Text
from .logger import auto_logger
import subprocess
import platform
import psutil
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


def get_file_size(path):
    size = os.path.getsize(path)
    logger.info(f"'{path}' size was received")
    return {
        "bytes": size,
        "kb": round(size / 1024, 2),
        "mb": round(size / (1024**2), 2),
        "gb": round(size / (1024**3), 4)
    }



def get_folder_size(folder_path):
    total_size = 0
    for root,dirs,files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root,file)

            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)

    logger.info(f"'{folder_path}' size was received")
    return {
        "bytes": total_size,
        "kb": round(total_size / 1024, 2),
        "mb": round(total_size / (1024**2), 2),
        "gb": round(total_size / (1024**3), 4)
    }


def get_system_details():
    mem = psutil.virtual_memory()
    
    total = mem.total / (1024**3)
    available = mem.available / (1024**3)
    percent = mem.percent

    logical_cores = psutil.cpu_count(logical=True)
    physical_cores = psutil.cpu_count(logical=False)


    logger.info("System information has been received")

    return {
        "total_gb": round(total, 2),
        "available_gb": round(available, 2),
        "percent": round(percent, 2),
        "logical": logical_cores,
        "physical": physical_cores
    }