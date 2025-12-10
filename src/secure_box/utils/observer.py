from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from time import sleep
from .logger import auto_logger
import os


logger = auto_logger()


class FolderObserver(FileSystemEventHandler):
    def __init__(self, path='.',checkTem=False):
        self.path = path
        self.isChanged = False
        self.initial_snapshot = self.snapshot_folder(path)
        self.current_snapshot = self.initial_snapshot.copy()

    def snapshot_folder(self, path):
        """
        Take a snapshot of the folder
        """
        snapshot = {}
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    stat = os.stat(fp)
                    snapshot[fp] = (stat.st_size, stat.st_mtime)
                except FileNotFoundError:
                    pass
        return snapshot

    def on_any_event(self, event):
        self.isChanged = True

    def check_differences(self):
        new_snapshot = self.snapshot_folder(self.path)

        old = set(self.initial_snapshot.keys())
        new = set(new_snapshot.keys())

        added = new - old
        removed = old - new

        modified = {
            f for f in (old & new)
            if self.initial_snapshot[f] != new_snapshot[f]
        }

        return added, removed, modified


if __name__ == "__main__":
    PATH = '.'
    handler = FolderObserver(path=PATH)
    observer = Observer()

    observer.schedule(handler, path=PATH, recursive=True)
    observer.start()

    print("Watching folder:", PATH)
    try:
        while True:
            sleep(1)

            if handler.isChanged:
                handler.isChanged = False
                added, removed, modified = handler.check_differences()
                if added or removed or modified:
                    logger.info("Changes detected:")

    except KeyboardInterrupt:
        observer.stop()

    observer.join()
