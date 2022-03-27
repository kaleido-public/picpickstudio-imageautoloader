from email.policy import default
from turtle import position
import click
from pathlib import Path
import re
import marshmallow.exceptions
import yaml
import multiprocessing
import asyncio
import PIL.Image
from picpickstudio_imageautoloader.config import AppConfig
from picpickstudio_imageautoloader.window_watcher import WindowWatcher
from picpickstudio_imageautoloader.dir_watcher import DirWatcher
import PySimpleGUI as sg
import io
import time


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
    currently_displayed: Path | None
    state = PreviewWindowState()

    def __init__(self) -> None:
        self.window = None
        self.currently_displayed = None

    @staticmethod
    def preview_image(file: Path) -> sg.Window:
        layout = [sg.Image]
        image = PIL.Image.open(file)
        png = io.BytesIO()
        image.save(png, format="png")
        layout = [[sg.Image(data=png.getvalue(), enable_events=True, expand_y=True)]]
        window = sg.Window(
            "Window Title",
            layout,
            return_keyboard_events=True,
            finalize=True,
            no_titlebar=False,
            grab_anywhere=True,
            resizable=True,
            element_justification="c",
            background_color="#000000",
        )
        return window

    def update_image(self) -> None:
        next_file = self.state.get_next_file()
        if next_file is None:
            self.close_window()
        elif next_file != self.currently_displayed:
            self.open_window(next_file)

    def close_window(self) -> None:
        if self.window:
            self.window.close()
            self.window = None

    def open_window(self, file: Path) -> None:
        print(f"Open preview: {file}")
        self.close_window()
        self.window = self.preview_image(file)
        self.currently_displayed = file

    async def start(self) -> None:
        await asyncio.to_thread(self.event_loop)
        print("Image preview exits")

    def stop(self) -> None:
        self.state.set_stop()

    def event_loop(self) -> None:
        """This is meant to run from a different thread."""
        while True:  # Event Loop
            needs_update = False
            if self.window:
                event, values = self.window.read(timeout=1000, timeout_key=-1)
                match event:
                    case -1:
                        needs_update = True
                    case "Escape:27":
                        break
                    case sg.WIN_CLOSED:
                        break
            else:
                time.sleep(1)
                needs_update = True
            if needs_update:
                self.update_image()
            if self.state.get_stop():
                break
        self.close_window()
        exit("Image previewer stopped")
