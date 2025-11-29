import os
import json
import hashlib
import time
import tempfile
from .logger import logger


class SafeBackupWriter:
    def __init__(self,out_path):
        self.out_path = out_path
        self.hash_path = out_path + ".sha256"
        self.state_path = out_path + ".state"
    

    def sha256_file(self, path):
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024*1024)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()
    

    def write_state(self, status):
        state = {
            "status": status,
            "timestamp": time.time(),
            "target": self.out_path,
        }

        with open(self.state_path, "w") as f:
            json.dump(state, f,indent=4)

    
    def cleanup_incomplete(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, "r") as f:
                state = json.load(f)

            if state["status"] == "in-progress":
                logger.info("Cleaning up incomplete backup...")

                os.remove(self.state_path)
    
    def write_backup(self, writer_function):
        self.cleanup_incomplete()
        self.write_state("in-progress")

        try:
            tmp_dir = os.path.dirname(self.out_path)
            with tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False) as tmp:
                tmp_path = tmp.name

            writer_function(tmp_path)
            file_hash = self.sha256_file(tmp_path)
            os.replace(tmp_path,self.out_path)

            with open(self.hash_path,"w") as f:
                f.write(file_hash)

            self.write_state("completed")
            logger.info("Backup sucsessfully complated!")
            
        except Exception as e:
            logger.warning("Backup failed:",e)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)