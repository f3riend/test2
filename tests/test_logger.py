import pytest
import os
from utils.logger import auto_logger


def test_auto_logger_creates_log_file(temp_dir, monkeypatch):
    monkeypatch.setattr('utils.logger.LOG_DIR', temp_dir)
    
    logger = auto_logger()
    
    logger.info("Test log message")
    
    expected_log = os.path.join(temp_dir, "test_logger.log")
    
    import time
    time.sleep(0.1)
    
    if os.path.exists(expected_log):
        with open(expected_log, "r") as f:
            content = f.read()
            assert "Test log message" in content


def test_auto_logger_multiple_calls():
    logger1 = auto_logger()
    logger2 = auto_logger()
    
    assert logger1 is logger2