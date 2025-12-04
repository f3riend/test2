from .lock import Lock
from .tools import ASCIIBar
from .backup import SafeBackupWriter
from .logger import auto_logger
from rich.progress import Progress, TextColumn, TimeElapsedColumn
import subprocess
import platform
import tempfile
import tarfile
import shutil
import os


logger = auto_logger()

class Unlock(Lock):
    def __init__(self, password, data_file="data"):
        self.password = password
        self.data_file = data_file + ".bin"
        self.chunk_size = 8 * 1024 * 1024
        self.key = self.password_to_key(password)
        
        self.system = platform.system()
        self.temp_dir = None
        self.enc_path = None
        self.tar_path = None

    def _setup_temp_directory(self):
        """Create a temporary directory"""
        if self.system == "Windows":
            temp_root = "C:\\Temp"
            if not os.path.exists(temp_root):
                os.makedirs(temp_root)
        else:
            temp_root = tempfile.gettempdir()
        
        self.temp_dir = tempfile.mkdtemp(prefix="SECURE_", dir=temp_root)
        self.enc_path = os.path.join(self.temp_dir, "enc.bin")
        self.tar_path = os.path.join(self.temp_dir, "data.tar")

    def _copy_in_chunks(self, src, dst, chunk_size=8*1024*1024):
        """Memory-efficient file copy"""
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                chunk = fsrc.read(chunk_size)
                if not chunk:
                    break
                fdst.write(chunk)

    def _cleanup_temp(self):
        """Clear temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            def remove_readonly(func, path, excinfo):
                os.chmod(path, 0o777)
                func(path)
            
            shutil.rmtree(self.temp_dir, onerror=remove_readonly)

    def decrypt_stream(self, in_path, out_path, key):
        """Decrypt the encrypted file"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key)
        total_size = os.path.getsize(in_path)
        
        with Progress(
            TextColumn("🔓 Decrypting "),
            ASCIIBar(),
            TextColumn("{task.percentage:>5.1f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("decrypt", total=total_size)
            
            with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
                while True:
                    len_bytes = fin.read(4)
                    if not len_bytes:
                        break
                    
                    block_len = int.from_bytes(len_bytes, "big")
                    nonce = fin.read(12)
                    enc = fin.read(block_len)
                    
                    dec = aes.decrypt(nonce, enc, None)
                    fout.write(dec)
                    
                    progress.update(task, advance=4 + 12 + block_len)

    def extract_tar_stream(self, tar_path, out_dir):
        """Open the TAR archive"""
        with tarfile.open(tar_path, "r") as tar:
            members = tar.getmembers()
            
            with Progress(
                TextColumn("📂 Extracting "),
                ASCIIBar(),
                TextColumn("{task.percentage:>5.1f}%"),
                TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task("extract", total=len(members))
                
                for member in members:
                    tar.extract(member, path=out_dir)
                    progress.update(task, advance=1)

    def open_folder(self):
        """Open the folder for user"""
        if self.system == "Windows":
            subprocess.Popen(f'explorer "{self.temp_dir}"')
        else:
            subprocess.Popen(["xdg-open", self.temp_dir])

    def run(self):
        """Main process"""
        if not os.path.exists(self.data_file):
            logger.info(f"{self.data_file} not found")
            return
        
        self._setup_temp_directory()
        

        logger.info("[+] Preparing decryption...")
        self._copy_in_chunks(self.data_file, self.enc_path)
        
        logger.info("[+] The password is decoding...")
        try:
            self.decrypt_stream(self.enc_path, self.tar_path, self.key)
        except Exception as e:
            logger.warning(f"Password is wrong or data is corrupted, error: {e}")
            self._cleanup_temp()
            return
        
        logger.info("[+] TAR extracting...")
        self.extract_tar_stream(self.tar_path, self.temp_dir)
        
        logger.info("[+] Folder is opened...")
        self.open_folder()
        
        input("\nPress enter to close the folder...")
        
        logger.info("[+] TAR is creating...")
        self.create_tar_stream(self.temp_dir, self.tar_path)
        
        logger.info("[+] Encrypting (safe)...")
        safe = SafeBackupWriter(self.data_file)

        def encrypt_tmp(tmp_path, checkpoint):
            self.encrypt_stream(self.tar_path, tmp_path, self.key)
        
        safe.write_backup(encrypt_tmp)

        logger.info("Data updated successfully")
        
        self._cleanup_temp()
        logger.info("[✓] Cleanup completed")


if __name__ == "__main__":
    import getpass
    
    password = getpass.getpass("Password: ")
    unlocker = Unlock(password, data_file="second")
    unlocker.run()