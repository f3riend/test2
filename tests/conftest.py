import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir



@pytest.fixture
def sample_file(temp_dir):
    file_path = os.path.join(temp_dir,"sample.txt")
    with open(file_path,"w") as f:
        f.write("Test data\n" * 100)
    
    return file_path


@pytest.fixture
def sample_folder(temp_dir):
    folder_path = os.path.join(temp_dir,"test_folder")
    os.makedirs(folder_path)


    for i in range(3):
        file_path = os.path.join(folder_path,f"file{i}.txt")
        with open(file_path,"w") as f:
            f.write(f"Content {i}\n" * 50)
    
    return folder_path


@pytest.fixture
def test_password():
    return "test_password_123"