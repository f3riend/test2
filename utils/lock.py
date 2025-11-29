from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .tools import ASCIIBar
from .backup import SafeBackupWriter
from .logger import logger
from rich.progress import Progress, TextColumn, TimeElapsedColumn
import datetime
import hashlib
import tarfile
import os


class Lock:
    def __init__(self, password, folder,name="data"):
        self.password = password
        self.folder = folder
        self.output = name + ".bin"
        self.tar_path = name + ".tar"
        self.chunk_size = 32 * 1024 * 1024
        
        self.key = self.password_to_key(password)
    
    def password_to_key(self, pw):
        """Convert the password to an AES key"""
        return hashlib.sha256(pw.encode()).digest()
    
    def get_folder_size(self, folder):
        """Calculate folder size"""
        total = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                total += os.path.getsize(os.path.join(root, file))
        return total
    
    def create_tar_stream(self, folder, path):
        """Convert the folder to a TAR archive"""
        total_size = self.get_folder_size(folder)
        
        with Progress(
            TextColumn("📦 Archive is being created "),
            ASCIIBar(),
            TextColumn(" {task.percentage:>5.1f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("tar", total=total_size)
            
            with tarfile.open(path, "w") as tar:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, folder)
                        file_size = os.path.getsize(full_path)
                        
                        tar.add(full_path, arcname=arcname)
                        progress.update(task, advance=file_size)
    
    def encrypt_stream(self, path, outpath, key):
        """Encrypt the file"""
        aes = AESGCM(key)
        total_size = os.path.getsize(path)
        
        with Progress(
            TextColumn("🔒 Encrypting "),
            ASCIIBar(),
            TextColumn(" {task.percentage:>5.1f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("enc", total=total_size)
            
            with open(path, 'rb') as fin, open(outpath, 'wb') as fout:
                while True:
                    chunk = fin.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    nonce = os.urandom(12)
                    enc = aes.encrypt(nonce, chunk, None)
                    
                    fout.write(len(enc).to_bytes(4, 'big'))
                    fout.write(nonce)
                    fout.write(enc)
                    
                    progress.update(task, advance=len(chunk))
    
    def run(self):
        logger.info("[+] Folder is being packed...")
        self.create_tar_stream(self.folder, self.tar_path)

        logger.info("[+] Encrypting (safe)...")

        safe = SafeBackupWriter(self.output)

        def encrypt_to_tmp(tmp_path):
            self.encrypt_stream(self.tar_path, tmp_path, self.key)

        safe.write_backup(encrypt_to_tmp)

        os.remove(self.tar_path)

        logger.info("[✓] Safe backup created:", self.output)




if __name__ == "__main__":
    import getpass
    
    password = getpass.getpass("Password: ")
    folder = input("Folder name: ")
    
    locker = Lock(password, folder)
    locker.run()