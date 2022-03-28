from email.policy import default
from fileinput import filename
from tkinter.messagebox import NO
from turtle import position
from typing import Any, Callable, Tuple, final
import click
from pathlib import Path
import re
import marshmallow.exceptions
from numpy import full
import yaml
import multiprocessing
import asyncio
import PIL.Image
import PySimpleGUI as sg
import io
import time
import traceback


class PreviewWindowState:
    lock = multiprocessing.Lock()
    file: None | Path = None
    should_stop: bool = False

    def get_next_file(self):
        with self.lock:
            return self.file

    def set_next_file(self, val: Path | None):
        with self.lock:
            self.file = val

    def set_stop(self):
        with self.lock:
            self.should_stop = True

    def get_stop(self):
        with self.lock:
            return self.should_stop


class ImagePreviewer:
    window: sg.Window | None
    window_image: sg.Image | None
    currently_displayed: Path | None
    is_fullscreen: bool
    state = PreviewWindowState()

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.window = None
        self.window_image = None
        self.currently_displayed = None
        self.is_fullscreen = False

    def update_image_tick(self) -> None:
        # if not self.should_process_tick():
        #     return
        next_file = self.state.get_next_file()
        if next_file != self.currently_displayed:
            if next_file is None:
                self.hide_window()
            else:
                self.open_window(next_file, fullscreen=self.is_fullscreen)

    def close_window(self) -> None:
        if self.window:
            self.window.close()
            self.window = None
            self.window_image = None
            self.is_fullscreen = False
            self.currently_displayed = None

    def hide_window(self) -> None:
        if self.window:
            self.window.minimize()

    def window_is_minimized(self) -> bool:
        assert self.window
        return self.window.TKroot.state() == "iconic"

    def should_process_tick(self) -> bool:
        return self.is_fullscreen

    def update_window_image(self, file: Path) -> None:
        if self.window_image:
            self.currently_displayed = file
            self.window_image.update(data=open_image(file))

    def show_window(self, file: Path, fullscreen: bool = False) -> None:
        """Use an existing window to display a file."""
        assert self.window, "Use open window"
        self.update_window_image(file)
        if fullscreen:
            self.window.maximize()
        else:
            self.window.normal()

    def open_window(self, file: Path, fullscreen: bool = False) -> None:
        """Display the file in a window. Use existing window if possible,
        otherwise open a new window."""
        print(f"Open preview: {file}")
        if self.window:
            self.show_window(file, fullscreen=fullscreen)
        else:
            self.window, self.window_image = create_window(file, fullscreen=fullscreen)
            self.currently_displayed = file

    async def start(self) -> None:
        try:
            welcome_img = Path("./resources/welcome.png")
            self.currently_displayed = welcome_img
            self.state.set_next_file(welcome_img)
            self.open_window(welcome_img, fullscreen=False)
            await asyncio.gather(
                self.update_image_loop(),
                self.window_event_loop(),
            )
        except BaseException:
            self.state.set_stop()
            self.clean_up()
            raise

    def stop(self) -> None:
        self.state.set_stop()

    async def update_image_loop(self) -> None:
        while True:  # Event Loop
            try:
                if self.state.get_stop():
                    self.clean_up()
                    break  # exit event loop
                self.update_image_tick()
            except Exception:
                traceback.print_exc()
            finally:
                await asyncio.sleep(self.interval)

    async def window_event_loop(self) -> None:
        while True:
            try:
                if self.window is None:
                    await asyncio.sleep(self.interval)
                else:
                    event, values = self.window.read(timeout=1, timeout_key=-1)
                    if event == -1:  # timeout
                        if self.state.get_stop():
                            self.clean_up()
                            break  # exit event loop
                        else:
                            await asyncio.sleep(0.1)
                    else:
                        self.handle_window_event(self.window, event, values)
            except Exception:
                traceback.print_exc()
                await asyncio.sleep(self.interval)

    def clean_up(self) -> None:
        self.close_window()
        print("Image previewer stopped")

    def set_window_max(self):
        """Reopen the current window without the title bar"""
        if self.window:
            if not self.window.NoTitleBar:
                currently_displayed = self.currently_displayed
                self.close_window()
                self.open_window(currently_displayed, fullscreen=True)
                self.is_fullscreen = True

    def set_window_normal(self):
        """Reopen the current window with the title bar"""
        if self.window:
            if self.window.NoTitleBar:
                currently_displayed = self.currently_displayed
                self.close_window()
                self.open_window(currently_displayed, fullscreen=False)
                self.is_fullscreen = False

    def handle_window_event(self, window: sg.Window, event, values) -> None:
        match event:
            case sg.WIN_CLOSED:
                self.close_window()
            case "Escape:27":
                if window.TKroot.state() == "zoomed":
                    self.set_window_normal()
            case "Configure":
                if window.TKroot.state() == "zoomed":
                    self.set_window_max()
            case _:
                print(event, values)


def open_image(file: Path) -> bytes:
    image = PIL.Image.open(file)
    png = io.BytesIO()
    image.save(png, format="png")
    return png.getvalue()


def create_window(file: Path, fullscreen: bool = False) -> Tuple[sg.Window, sg.Image]:
    png = open_image(file)
    image = sg.Image(data=png, enable_events=True, expand_y=True)
    layout = [[image]]
    window = sg.Window(
        "PICPICK PREVIEW",
        layout,
        return_keyboard_events=True,
        no_titlebar=fullscreen,
        grab_anywhere=True,
        resizable=(not fullscreen),
        element_justification="c",
        background_color="#000000",
        keep_on_top=True,
    )
    window.finalize()
    if fullscreen:
        window.maximize()
    window.bind("<Configure>", "Configure")
    return (window, image)
