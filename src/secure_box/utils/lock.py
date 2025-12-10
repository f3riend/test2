from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .tools import ASCIIBar
from .backup import SafeBackupWriter
from .logger import auto_logger
from .config import lock_auto_config
from rich.progress import Progress, TextColumn, TimeElapsedColumn
import datetime
import hashlib
import tarfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


logger = auto_logger()


class Lock:
    def __init__(self, password, folder, name="data"):  
        self.password = password
        self.folder = folder
        self.output = name + ".bin"
        self.tar_path = name + ".tar"

        chunk,worker = lock_auto_config(folder=folder)
        
        self.chunk_size = chunk
        self.max_workers = worker
        
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
    
    def _encrypt_chunk(self, chunk_data, chunk_index):
        """
        Encrypt a single chunk (thread-safe)
        
        Returns: (chunk_index, encrypted_data)
        """
        aes = AESGCM(self.key)
        nonce = os.urandom(12)
        enc = aes.encrypt(nonce, chunk_data, None)
        

        result = len(enc).to_bytes(4, 'big') + nonce + enc
        
        return (chunk_index, result)
    
    def encrypt_stream_parallel(self, path, outpath, checkpoint=None):
        """
        Encrypt file using parallel threads
        
        Args:
            path: Input file
            outpath: Output file
            checkpoint: Resume checkpoint
        """
        total_size = os.path.getsize(path)
        

        start_position = 0
        start_chunk_index = 0
        
        if checkpoint:
            start_position = checkpoint.get('bytes_written', 0)
            start_chunk_index = checkpoint.get('chunk_index', 0)
            logger.info(f"Resuming from byte {start_position}, chunk {start_chunk_index}")
        
        with Progress(
            TextColumn("🔒 Encrypting (multi-threaded) "),
            ASCIIBar(),
            TextColumn(" {task.percentage:>5.1f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("enc", total=total_size)
            
            if start_position > 0:
                progress.update(task, completed=start_position)
            
            mode = 'ab' if checkpoint else 'wb'
            
            with open(path, 'rb') as fin, open(outpath, mode) as fout:
                if start_position > 0:
                    fin.seek(start_position)
                
                bytes_written = start_position
                chunk_index = start_chunk_index
                write_lock = threading.Lock()
                

                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {}
                    chunks_to_process = []
                    
                    while True:
                        chunk_data = fin.read(self.chunk_size)
                        if not chunk_data:
                            break
                        

                        future = executor.submit(
                            self._encrypt_chunk, 
                            chunk_data, 
                            chunk_index
                        )
                        futures[future] = chunk_index
                        chunks_to_process.append((chunk_index, len(chunk_data)))
                        chunk_index += 1
                        
                        if len(futures) >= self.max_workers * 2:
                            self._write_completed_chunks(
                                futures, fout, progress, task, 
                                write_lock, bytes_written, chunk_index
                            )
                    
                    for future in as_completed(futures):
                        idx, encrypted = future.result()
                        
                        with write_lock:
                            fout.write(encrypted)
                            
                            original_size = next(
                                size for i, size in chunks_to_process if i == idx
                            )
                            bytes_written += original_size
                            progress.update(task, advance=original_size)
                            

                            if idx % 10 == 0:
                                safe = SafeBackupWriter(self.output)
                                safe.write_checkpoint(bytes_written, idx)
    
    def encrypt_stream(self, path, outpath, key, checkpoint=None):
        """
        Single-threaded encryption (fallback)
        """
        aes = AESGCM(key)
        total_size = os.path.getsize(path)
        
        start_position = 0
        chunk_index = 0
        
        if checkpoint:
            start_position = checkpoint.get('bytes_written', 0)
            chunk_index = checkpoint.get('chunk_index', 0)
            logger.info(f"Resuming from byte {start_position}, chunk {chunk_index}")
        
        buffer = bytearray(self.chunk_size)
        
        with Progress(
            TextColumn("🔒 Encrypting "),
            ASCIIBar(),
            TextColumn(" {task.percentage:>5.1f}%"),
            TimeElapsedColumn(),
        ) as progress:
            task = progress.add_task("enc", total=total_size)
            
            if start_position > 0:
                progress.update(task, completed=start_position)
            
            mode = 'ab' if checkpoint else 'wb'
            
            with open(path, 'rb') as fin, open(outpath, mode) as fout:
                if start_position > 0:
                    fin.seek(start_position)
                
                bytes_written = start_position
                
                while True:
                    bytes_read = fin.readinto(buffer)
                    if bytes_read == 0:
                        break
                    
                    nonce = os.urandom(12)
                    enc = aes.encrypt(nonce, buffer[:bytes_read], None)
                    
                    fout.write(len(enc).to_bytes(4, 'big'))
                    fout.write(nonce)
                    fout.write(enc)
                    
                    bytes_written += bytes_read
                    chunk_index += 1
                    
                    progress.update(task, advance=bytes_read)
                    
                    if chunk_index % 10 == 0:
                        safe = SafeBackupWriter(self.output)
                        safe.write_checkpoint(bytes_written, chunk_index)
    
    def run(self, resume=False, use_threading=True):
        """
        Run lock process
        
        Args:
            resume: Resume from checkpoint
            use_threading: Use multi-threaded encryption
        """
        logger.info("[+] Folder is being packed...")
        
        if not resume or not os.path.exists(self.tar_path):
            self.create_tar_stream(self.folder, self.tar_path)
        else:
            logger.info("[+] Using existing TAR file for resume")

        logger.info(f"[+] Encrypting (safe, threads={self.max_workers if use_threading else 1})...")

        safe = SafeBackupWriter(self.output)

        def encrypt_to_tmp(tmp_path, checkpoint):
            if use_threading:
                self.encrypt_stream_parallel(self.tar_path, tmp_path, checkpoint)
            else:
                self.encrypt_stream(self.tar_path, tmp_path, self.key, checkpoint)

        safe.write_backup(encrypt_to_tmp, resume=resume)

        if os.path.exists(self.tar_path):
            os.remove(self.tar_path)

        logger.info("[✓] Safe backup created:", self.output)