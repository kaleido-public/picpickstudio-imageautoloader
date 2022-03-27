from typing import TYPE_CHECKING, Any, Iterable, List, NewType, Tuple, Protocol

HWND = int

class CaptureWindowOutput(Protocol):
    frame: Any
    size: Size

class Size(Protocol):
    width: int
    height: int

def captureWindowBitBlt(window: HWND) -> CaptureWindowOutput: ...
def captureWindowWinRT(window: HWND) -> CaptureWindowOutput: ...
