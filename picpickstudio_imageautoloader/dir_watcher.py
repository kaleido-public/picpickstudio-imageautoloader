from typing import Callable
from pathlib import Path
import re
import watchdog.observers
import watchdog.events


class DirWatcher:
    def __init__(
        self,
        path: Path,
        on_new_file: Callable[[Path], None],
        filename_regex: re.Pattern,
    ) -> None:
        self.path = path
        self.on_new_file = on_new_file
        self.filename_regex = filename_regex

    class __FileSystemEventHandler(watchdog.events.FileSystemEventHandler):
        def __init__(self, dirobserver: "DirWatcher") -> None:
            super().__init__()
            self.watcher = dirobserver

        def on_created(self, event: watchdog.events.FileCreatedEvent) -> None:
            if self.watcher.filename_regex.match(
                Path(event.src_path).name, re.IGNORECASE
            ):
                try:
                    self.watcher.on_new_file(Path(event.src_path))
                except Exception as e:
                    print(e)

    def start(self) -> None:
        self.observer = watchdog.observers.Observer()
        self.observer.schedule(
            self.__FileSystemEventHandler(dirobserver=self),
            path=self.path,
            recursive=True,
        )
        print(f"Watching {self.path.absolute()} for {self.filename_regex.pattern}")
        self.observer.start()

    def stop(self) -> None:
        self.observer.stop()
        print("Dir watcher stopped")
