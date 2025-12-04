import psutil
import os


def get_file_size(path):
    size = os.path.getsize(path)
    return {
        "bytes": size,
        "kb": round(size / 1024, 2),
        "mb": round(size / (1024**2), 2),
        "gb": round(size / (1024**3), 4)
    }


def getSystemDetails():
    mem = psutil.virtual_memory()
    
    total = mem.total / (1024**3)
    available = mem.available / (1024**3)
    percent = mem.percent

    logical_cores = psutil.cpu_count(logical=True)
    physical_cores = psutil.cpu_count(logical=False)


    return {
        "total_gb": round(total, 2),
        "available_gb": round(available, 2),
        "percent": round(percent, 2),
        "logical": logical_cores,
        "physical": physical_cores
    }


