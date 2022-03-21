import re
from typing import Callable
import sys


class WindowWatcher:
    def __init__(self, title_regex: re.Pattern, on_change: Callable[..., None]) -> None:
        self.title_regex = title_regex
        self.on_change = on_change
        match sys.platform:
            case "win32":
                from .window_watcher_win32 import WindowWatcherWin32

                self.delegate = WindowWatcherWin32(self)
            case platform:
                raise NotImplementedError(f"{platform} not supported.")

    def start(self) -> None:
        self.delegate.start()
