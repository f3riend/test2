import pytest
import os
import json
import time
from secure_box.utils.backup import SafeBackupWriter

def test_backup_writer_initialization(temp_dir):
    out_path = os.path.join(temp_dir, "test.bin")
    writer = SafeBackupWriter(out_path)

    assert writer.out_path == out_path
    assert writer.hash_path == out_path + ".sha256"
    assert writer.state_path == out_path + ".state"
    assert writer.checkpoint_path == out_path + ".checkpoint"



def test_sha256_file(temp_dir):
    test_file = os.path.join(temp_dir, "test.txt")
    with open(test_file, "wb") as f:
        f.write(b"Hello World")

    
    writer = SafeBackupWriter("dummy")
    hash_result = writer.sha256_file(test_file)

    expected = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    assert hash_result == expected


def test_write_state(temp_dir):
    out_path = os.path.join(temp_dir, "test.bin")
    writer = SafeBackupWriter(out_path)

    writer.write_state("in-progress", progress={"chunk": 5})

    assert os.path.exists(writer.state_path)

    with open(writer.state_path, "r") as f:
        state = json.load(f)

    
    assert state["status"] == "in-progress"
    assert state["target"] == out_path
    assert state["progress"]["chunk"] == 5
    assert "timestamp" in state


def test_checkpoint_save_and_load(temp_dir):
    out_path = os.path.join(temp_dir, "test.bin")
    writer = SafeBackupWriter(out_path)

    writer.write_checkpoint(bytes_written=1024000, chunk_index=10)
    
    assert os.path.exists(writer.checkpoint_path)

    checkpoint = writer.load_checkpoint()
    assert checkpoint is not None
    assert checkpoint["bytes_written"] == 1024000
    assert checkpoint["chunk_index"] == 10
    assert checkpoint["target"] == out_path


def test_checkpoint_clear(temp_dir):
    out_path = os.path.join(temp_dir, "test.bin")
    writer = SafeBackupWriter(out_path)

    writer.write_checkpoint(1000, 5)
    assert os.path.exists(writer.checkpoint_path)

    writer.clear_checkpoint()
    assert not os.path.exists(writer.checkpoint_path)



def test_write_backup_success(temp_dir):
    out_path = os.path.join(temp_dir, "backup.bin")
    writer = SafeBackupWriter(out_path)

    def simple_writer(tmp_path, checkpoint):
        with open(tmp_path, "wb") as f:
            f.write(b"Test backup content")
    
    writer.write_backup(simple_writer, resume=False)

    assert os.path.exists(out_path)
    assert os.path.exists(writer.hash_path)
    assert os.path.exists(writer.state_path)


    with open(writer.state_path, "r") as f:
        state = json.load(f)
    assert state["status"] == "completed"


    with open(writer.hash_path, "r") as f:
        saved_hash = f.read()

    actual_hash = writer.sha256_file(out_path)
    assert saved_hash == actual_hash



def test_write_backup_with_resume(temp_dir):
    out_path = os.path.join(temp_dir, "backup.bin")
    writer = SafeBackupWriter(out_path)

    writer.write_checkpoint(512, 1)
    writer.write_state("in-progress")

    call_count = []

    def resume_writer(tmp_path, checkpoint):
        call_count.append(1)
        if checkpoint:
            assert checkpoint["bytes_written"] == 512
            assert checkpoint["chunk_index"] == 1
        
        with open(tmp_path, "wb") as f:
            f.write(b"Resumed content")
    
    writer.write_backup(resume_writer, resume=True)
    assert len(call_count) == 1
    assert not os.path.exists(writer.checkpoint_path)


def test_write_backup_failure_cleanup(temp_dir):
    out_path = os.path.join(temp_dir, "backup.bin")
    writer = SafeBackupWriter(out_path)

    def failing_writer(tmp_path, checkpoint):
        with open(tmp_path, "wb") as f:
            f.write(b"Partial content")
        raise Exception("Simulated failure")
    

    with pytest.raises(Exception, match="Simulated failure"):
        writer.write_backup(failing_writer)


    assert not os.path.exists(out_path)