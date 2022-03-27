from typing import TYPE_CHECKING, Iterable, List, NewType, Tuple

import windowcapture_win_py
import win32api
import win32gui
from dataclasses import dataclass
import PIL.Image
from PIL.Image import Image
import PIL.ImageChops
import re
import asyncio

if TYPE_CHECKING:
    from .window_watcher import WindowWatcher

HWND = int


@dataclass
class Size:
    width: int
    height: int


class WindowWatcherWin32:
    hwnd: HWND | None
    last_capture: Image | None
    parent: "WindowWatcher"

    def __init__(self, parent: "WindowWatcher") -> None:
        self.parent = parent
        self.hwnd = None
        self.last_capture = None

    async def start(self) -> None:
        await asyncio.gather(
            self.update_hwnd_loop(),
            self.capture_window_loop(),
        )
        print("Window watcher exits")

    async def update_hwnd_loop(self) -> None:
        while True:
            window = find_window(self.parent.title_regex)
            if window:
                self.hwnd, title = window
                print(f'Window: {self.hwnd} "{title}"')
            else:
                print(f"Looking for window: {self.parent.title_regex}")
                self.hwnd = None
            await asyncio.sleep(5)

    async def capture_window_loop(self) -> None:
        while True:
            if self.hwnd:
                new_capture = capture_window(self.hwnd)
                if detect_difference(
                    self.last_capture,
                    new_capture,
                    self.parent.window_watcher_tolerance,
                ):
                    self.parent.on_change()
                self.last_capture = new_capture
            await asyncio.sleep(1)


def capture_window(hwnd: HWND) -> Image:
    output = windowcapture_win_py.captureWindowWinRT(hwnd)
    image = PIL.Image.frombytes(
        "RGB",
        (output.size.width, output.size.height),
        output.frame,
        "raw",
        "RGBX",
    )
    B, G, R = image.split()
    image = PIL.Image.merge("RGB", [R, G, B])
    return image


def find_window(title_regex: re.Pattern) -> Tuple[HWND, str] | None:
    for hwnd, title in list_windows():
        if title_regex.match(title):
            return (hwnd, title)
    return None


def list_windows() -> List[Tuple[HWND, str]]:
    ret = []

    def handle(hwnd, *args, **kargs):
        title = win32gui.GetWindowText(hwnd)
        ret.append((hwnd, title))

    win32gui.EnumWindows(handle, None)
    return ret


def detect_difference(old: Image, new: Image, tolerance: float) -> bool:
    if not old and not new:
        return False
    if not old and new:
        return True
    if old and not new:
        return True

    threshold = abs(255 * tolerance)

    diff = PIL.ImageChops.difference(old, new).point(
        lambda p: 0 if p < threshold else p
    )
    if diff.getbbox():
        return True  # images are different
    else:
        return False  # images are same
