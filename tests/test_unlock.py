# tests/test_unlock.py
import pytest
import os
import tarfile
from utils.unlock import Unlock
from utils.lock import Lock


def test_unlock_initialization(test_password):
    """Unlock başlatma testi"""
    unlocker = Unlock(test_password, "test_data")
    
    assert unlocker.password == test_password
    assert unlocker.data_file == "test_data.bin"
    assert unlocker.chunk_size == 8 * 1024 * 1024
    assert unlocker.key is not None


def test_unlock_temp_directory_setup(test_password, temp_dir):
    """Geçici dizin kurulum testi"""
    unlocker = Unlock(test_password, "dummy")
    unlocker._setup_temp_directory()
    
    assert unlocker.temp_dir is not None
    assert os.path.exists(unlocker.temp_dir)
    assert unlocker.enc_path is not None
    assert unlocker.tar_path is not None
    
    # Cleanup
    unlocker._cleanup_temp()
    assert not os.path.exists(unlocker.temp_dir)


def test_copy_in_chunks(test_password, sample_file, temp_dir):
    """Chunk'lar halinde kopyalama testi"""
    unlocker = Unlock(test_password, "dummy")
    
    dest = os.path.join(temp_dir, "copied.txt")
    unlocker._copy_in_chunks(sample_file, dest, chunk_size=1024)
    
    # Dosya kopyalandı mı?
    assert os.path.exists(dest)
    
    # İçerik aynı mı?
    with open(sample_file, "rb") as f1, open(dest, "rb") as f2:
        assert f1.read() == f2.read()


def test_decrypt_stream(sample_folder, test_password, temp_dir):
    """Decrypt stream testi"""
    # Önce encrypt et
    output_path = os.path.join(temp_dir, "encrypted")
    locker = Lock(test_password, sample_folder, output_path, max_workers=2)
    locker.run(use_threading=False)
    
    # Şimdi decrypt et
    unlocker = Unlock(test_password, output_path)
    enc_file = output_path + ".bin"
    dec_file = os.path.join(temp_dir, "decrypted.tar")
    
    unlocker.decrypt_stream(enc_file, dec_file, unlocker.key)
    
    # Decrypt edilmiş dosya var mı?
    assert os.path.exists(dec_file)
    assert os.path.getsize(dec_file) > 0
    
    # TAR dosyası geçerli mi?
    assert tarfile.is_tarfile(dec_file)


def test_extract_tar_stream(sample_folder, test_password, temp_dir):
    """TAR extract testi"""
    # Encrypt -> Decrypt yap
    output_path = os.path.join(temp_dir, "encrypted")
    locker = Lock(test_password, sample_folder, output_path, max_workers=2)
    locker.run(use_threading=False)
    
    unlocker = Unlock(test_password, output_path)
    enc_file = output_path + ".bin"
    dec_file = os.path.join(temp_dir, "decrypted.tar")
    
    unlocker.decrypt_stream(enc_file, dec_file, unlocker.key)
    
    # Extract et
    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_dir)
    
    unlocker.extract_tar_stream(dec_file, extract_dir)
    
    # Dosyalar extract edildi mi?
    extracted_files = os.listdir(extract_dir)
    assert len(extracted_files) > 0
    
    # Orijinal dosyalar var mı?
    for i in range(3):
        expected_file = os.path.join(extract_dir, f"file_{i}.txt")
        assert os.path.exists(expected_file)


def test_wrong_password_decrypt(sample_folder, test_password, temp_dir):
    """Yanlış password ile decrypt testi"""
    # Doğru password ile encrypt
    output_path = os.path.join(temp_dir, "encrypted")
    locker = Lock(test_password, sample_folder, output_path, max_workers=2)
    locker.run(use_threading=False)
    
    # Yanlış password ile decrypt dene
    wrong_password = "wrong_password_123"
    unlocker = Unlock(wrong_password, output_path)
    enc_file = output_path + ".bin"
    dec_file = os.path.join(temp_dir, "decrypted.tar")
    
    # Hata bekliyoruz (cryptography exception)
    with pytest.raises(Exception):  # InvalidTag veya benzeri
        unlocker.decrypt_stream(enc_file, dec_file, unlocker.key)