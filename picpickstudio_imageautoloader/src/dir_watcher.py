from typing import Callable
from pathlib import Path
import re
import watchdog.observers
import watchdog.events
import time


class DirWatcher:
    def __init__(
        self,
        use_polling: bool,
        path: Path,
        on_new_file: Callable[[Path], None],
        filename_regex: re.Pattern,
    ) -> None:
        self.path = path
        self.on_new_file = on_new_file
        self.use_polling = use_polling
        self.filename_regex = filename_regex

    class __FileSystemEventHandler(watchdog.events.FileSystemEventHandler):
        def __init__(self, dirobserver: "DirWatcher") -> None:
            super().__init__()
            self.watcher = dirobserver

        def on_created(self, event: watchdog.events.FileCreatedEvent) -> None:
            if self.watcher.filename_regex.match(Path(event.src_path).name):
                self.watcher.on_new_file(event.src_path)

    def start(self) -> None:
        self.observer = watchdog.observers.Observer()
        self.observer.schedule(
            self.__FileSystemEventHandler(dirobserver=self),
            path=self.path,
            recursive=False,
        )
        print(f"Watching {self.path.absolute()}")
        self.observer.start()
        while True:
            time.sleep(1)
