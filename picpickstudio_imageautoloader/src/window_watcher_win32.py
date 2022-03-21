from typing import TYPE_CHECKING

# import pywin64

if TYPE_CHECKING:
    from .window_watcher import WindowWatcher


class WindowWatcherWin32:
    def __init__(self, parent: "WindowWatcher") -> None:
        self.parent = parent

    def start(self) -> None:
        pass
