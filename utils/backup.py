import os
import json
import hashlib
import time
import tempfile
import shutil
from .logger import logger


class SafeBackupWriter:
    def __init__(self, out_path):
        self.out_path = out_path
        self.hash_path = out_path + ".sha256"
        self.state_path = out_path + ".state"
        self.checkpoint_path = out_path + ".checkpoint"  # YENİ
    
    def sha256_file(self, path):
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024*1024)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()
    
    def write_state(self, status, progress=None):
        """Write state with optional progress info"""
        state = {
            "status": status,
            "timestamp": time.time(),
            "target": self.out_path,
        }
        
        if progress is not None:
            state["progress"] = progress
        
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=4)
    
    def write_checkpoint(self, bytes_written, chunk_index):
        """Save checkpoint for resume capability"""
        checkpoint = {
            "bytes_written": bytes_written,
            "chunk_index": chunk_index,
            "timestamp": time.time(),
            "target": self.out_path
        }
        
        with open(self.checkpoint_path, "w") as f:
            json.dump(checkpoint, f, indent=4)
    
    def load_checkpoint(self):
        """Load checkpoint if exists"""
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, "r") as f:
                    checkpoint = json.load(f)
                    logger.info(f"Found checkpoint: {checkpoint['bytes_written']} bytes written")
                    return checkpoint
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
                return None
        return None
    
    def clear_checkpoint(self):
        """Clear checkpoint after successful completion"""
        if os.path.exists(self.checkpoint_path):
            os.remove(self.checkpoint_path)
    
    def cleanup_incomplete(self):
        """Clean up incomplete backup"""
        if os.path.exists(self.state_path):
            with open(self.state_path, "r") as f:
                state = json.load(f)

            if state["status"] == "in-progress":
                logger.info("Cleaning up incomplete backup...")
                os.remove(self.state_path)
                
                # Ask user if they want to resume
                if os.path.exists(self.checkpoint_path):
                    logger.info("Incomplete backup found. Use resume=True to continue.")
    
    def write_backup(self, writer_function, resume=False):
        """Write backup with resume capability"""
        checkpoint = None
        
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                logger.info(f"Resuming from chunk {checkpoint['chunk_index']}")
        
        if not checkpoint:
            self.cleanup_incomplete()
        
        self.write_state("in-progress", progress={"resumed": resume})
        tmp_path = None

        try:
            # Create temp file in SAME directory as output
            target_dir = os.path.dirname(os.path.abspath(self.out_path)) or '.'
            
            with tempfile.NamedTemporaryFile(
                delete=False, 
                dir=target_dir,  # Same directory prevents cross-device issues
                prefix=".tmp_securebox_",
                suffix=".bin"
            ) as tmp:
                tmp_path = tmp.name

            # Write to temp file
            writer_function(tmp_path, checkpoint)
            
            # Calculate hash
            file_hash = self.sha256_file(tmp_path)
            
            # Atomic move (handles cross-device automatically)
            shutil.move(tmp_path, self.out_path)
            
            # Write hash file
            with open(self.hash_path, "w") as f:
                f.write(file_hash)

            self.write_state("completed")
            self.clear_checkpoint()
            logger.info("Backup successfully completed!")
            
        except Exception as e:
            logger.warning(f"Backup failed: {e}")
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            raise