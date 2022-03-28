import re
from typing import Callable
import sys
import asyncio


class WindowWatcher:
    def __init__(
        self,
        title_regex: re.Pattern,
        on_change: Callable[..., None],
        tolerance: float,
        interval: float,
    ) -> None:
        self.title_regex = title_regex
        self.on_change = on_change
        self.tolerance = tolerance
        self.interval = interval
        match sys.platform:
            case "win32":
                from .window_watcher_win32 import WindowWatcherWin32

                self.delegate = WindowWatcherWin32(self)
            case platform:
                raise NotImplementedError(f"{platform} not supported.")

    async def start(self) -> None:
        await self.delegate.start()

    def stop(self) -> None:
        self.delegate.stop()
