#!/usr/bin/env python3.10

from email.policy import default
from lib2to3.pytree import Base
from turtle import position
from typing import final
import click
from pathlib import Path
import re
import marshmallow.exceptions
import yaml
import multiprocessing
import asyncio
import PIL.Image
from picpickstudio_imageautoloader.config import AppConfig
from picpickstudio_imageautoloader.image_previewer import ImagePreviewer
from picpickstudio_imageautoloader.window_watcher import WindowWatcher
from picpickstudio_imageautoloader.dir_watcher import DirWatcher
import PySimpleGUI as sg
import io
import traceback

window_title = "PICPICK PREVIEW"


@click.command()
@click.option(
    "--default-config",
    "is_show_default_config",
    is_flag=True,
    help="Print default config to stdout.",
)
@click.option("-c", "--config", "config_path", type=Path, required=False)
def main(
    is_show_default_config: bool,
    config_path: Path | None,
):
    if is_show_default_config:
        print_default_config()
        exit()

    config = get_config(config_path)

    window_watcher = WindowWatcher(
        title_regex=re.compile(config.window_watcher.title_regex, re.IGNORECASE),
        on_change=on_window_change,
        tolerance=config.window_watcher.tolerance,
        interval=config.window_watcher.interval,
    )
    dir_watcher = DirWatcher(
        on_new_file=on_new_file,
        filename_regex=re.compile(config.dir_watcher.filename_regex, re.IGNORECASE),
        path=Path(config.dir_watcher.watch_dirpath),
    )
    image_previewer = ImagePreviewer(interval=config.image_previewer.interval)

    async def main_loop():
        try:
            cancellable = asyncio.gather(
                window_watcher.start(),
                image_previewer.start(),
            )
            await cancellable
        except Exception as e:
            traceback.print_exc()
        except BaseException:
            print("Interrupt")
            cancellable.cancel()
        finally:
            dir_watcher.stop()
            image_previewer.stop()
            window_watcher.stop()

    dir_watcher.start()
    asyncio.run(main_loop())


def print_default_config():
    print(AppConfig.default().to_yaml(), end="")


def get_config(config_path: Path | None) -> AppConfig:
    """Returns the config object from the file path, or the default config
    object."""
    config = AppConfig.default()
    if config_path is not None:
        content = config_path.read_text()
        try:
            config = AppConfig.from_yaml(content)
        except marshmallow.exceptions.ValidationError as error:
            exit(
                "Invalid configuration file.\n\n"
                + yaml.dump(error.normalized_messages())
            )
    return config


def on_new_file(file: Path) -> None:
    # with lock:
    print(f"New file: {file}")
    ImagePreviewer.state.set_next_file(file)


def on_window_change() -> None:
    # with lock:
    print("Window changed")
    ImagePreviewer.state.set_next_file(None)


main()
