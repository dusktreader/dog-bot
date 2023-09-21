import time
import shlex
import subprocess
from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class RestartHandler(FileSystemEventHandler):

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None
        self.reload()

    def reload(self):
        logger.debug(f"Re-executing {self.command}")
        if self.process is not None:
            self.process.terminate()
        self.process = subprocess.Popen(shlex.split(self.command))

    def trigger(self, event):
        if not event.src_path.endswith(".py"):
            logger.debug("skipping changes to non .py file")
            return
        self.reload()

    def on_created(self, event):
        self.trigger(event)

    def on_modified(self, event):
        self.trigger(event)

    def on_moved(self, event):
        self.trigger(event)


def run():

    handler = RestartHandler("poetry run bot")
    observer = Observer()
    observer.schedule(handler, "bot", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
