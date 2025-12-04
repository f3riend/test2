from utils.lock import Lock
import pytest
import os


def test_password_to_key():
    lock = Lock("test123", "dummy", "dummy")
    key = lock.password_to_key("test123")

    assert len(key) == 32
    assert isinstance(key,bytes)


    key2 = lock.password_to_key("test123")
    assert key == key2

    key3 = lock.password_to_key("test456")
    assert key != key3



def test_lock_small_folder(sample_folder, test_password, temp_dir):
    output_path = os.path.join(temp_dir, "encrypted")

    locker = Lock(test_password, sample_folder, output_path, max_workers=2)
    locker.run(use_threading=False)

    assert os.path.exists(output_path + ".bin")
    assert os.path.exists(output_path + ".bin.sha256")

    assert os.path.getsize(output_path + ".bin") > 0


def test_lock_and_unlock_cycle(sample_folder, test_password, temp_dir):
    output_path = os.path.join(temp_dir, "encrypted")

    locker = Lock(test_password, sample_folder, output_path, max_workers=2)
    locker.run(use_threading=False)


    from utils.unlock import Unlock
    unlocker = Unlock(test_password, output_path)


    enc_file = output_path + ".bin"
    dec_file = os.path.join(temp_dir, "decrypted.tar")
    
    unlocker.decrypt_stream(enc_file, dec_file, unlocker.key)

    assert os.path.exists(dec_file)
    assert os.path.getsize(dec_file) > 0