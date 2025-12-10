from .tools import get_file_size,get_folder_size,get_system_details
import inspect
import os
import yaml


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")



def load_config():
    with open(CONFIG_PATH,"r",encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config







def lock_auto_config(folder):
    """
    Automatically determine optimal encryption parameters based on folder size,
    available RAM, and CPU cores.
    
    Args:
        folder (str): Path to the folder to be encrypted.
    
    Returns:
        dict: {'chunk_size': int (bytes), 'max_workers': int}
    """
    data = load_config()

    if data["mode"] != "auto":
        return {
            "chunk_size": data.get("chunk_size", 8 * 1024 * 1024),
            "max_workers": data.get("max_workers", 4)
        }

    size = get_folder_size(folder)
    folder_gb = size['gb']

    details = get_system_details()
    available_ram = details["available_gb"]
    logical_cores = details["logical"]

    min_chunk = 8
    max_chunk = 512
    chunk_size_mb = int(available_ram * 1024 / logical_cores / 2)

    if chunk_size_mb < min_chunk:
        chunk_size_mb = min_chunk
    elif chunk_size_mb > max_chunk:
        chunk_size_mb = max_chunk

    chunk_size_bytes = chunk_size_mb * 1024 * 1024

    max_workers = min(logical_cores, int(available_ram / 2))
    if max_workers < 2:
        max_workers = 2

    return (chunk_size_bytes,max_workers)


def unlock_auto_config():
    """
    Automatically determine optimal decryption chunk size based on available RAM.
    Decryption is mostly I/O bound, so no multi-threading adjustments are needed.
    
    Returns:
        dict: {"chunk_size": int (bytes)}
    """
    details = get_system_details()
    available_ram = details["available_gb"]


    if available_ram < 8:
        chunk_mb = 4
    elif available_ram < 16:
        chunk_mb = 8
    elif available_ram < 32:
        chunk_mb = 16
    elif available_ram < 64:
        chunk_mb = 32
    else:
        chunk_mb = 64

    chunk_bytes = chunk_mb * 1024 * 1024

    return chunk_bytes



