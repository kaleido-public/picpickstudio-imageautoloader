#!/usr/bin/env python3.10

from email.policy import default
from lib2to3.pytree import Base
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
from picpickstudio_imageautoloader.image_previewer import ImagePreviewer
from picpickstudio_imageautoloader.window_watcher import WindowWatcher
from picpickstudio_imageautoloader.dir_watcher import DirWatcher
import PySimpleGUI as sg
import io


window_title = "PICPICK PREVIEW"


@click.command()
@click.option("--default-config", is_flag=True, help="Print default config to stdout.")
@click.option("-c", "--config", type=Path, required=False)
def main(
    default_config: bool,
    config: Path | None,
):
    if default_config:
        print_default_config()
        exit()

    config_obj = get_config(config)

    window_watcher = WindowWatcher(
        title_regex=re.compile(config_obj.window_title_regex, re.IGNORECASE),
        on_change=on_window_change,
        window_watcher_tolerance=config_obj.window_watcher_tolerance,
    )
    dir_watcher = DirWatcher(
        use_polling=config_obj.use_polling,
        on_new_file=on_new_file,
        filename_regex=re.compile(config_obj.filename_regex, re.IGNORECASE),
        path=Path(config_obj.watch_dirpath),
    )
    image_previewer = ImagePreviewer()

    async def main_loop():
        await asyncio.gather(
            window_watcher.start(),
            image_previewer.start(),
        )

    try:
        dir_watcher.start()
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        dir_watcher.stop()
        image_previewer.stop()
        exit("Interrupted")

    print("exit normally")


def print_default_config():
    print(AppConfig.default_config().to_yaml(), end="")


def get_config(config_path: Path | None) -> AppConfig:
    """Returns the config object from the file path, or the default config
    object."""
    config_obj = AppConfig.default_config()
    if config_path is not None:
        content = config_path.read_text()
        try:
            config_obj = AppConfig.from_yaml(content)
        except marshmallow.exceptions.ValidationError as error:
            exit(
                "Invalid configuration file.\n\n"
                + yaml.dump(error.normalized_messages())
            )
    return config_obj


def on_new_file(file: Path) -> None:
    # with lock:
    print(f"New file: {file}")
    ImagePreviewer.state.set_next_file(file)


def on_window_change() -> None:
    # with lock:
    print("Window changed")
    ImagePreviewer.state.set_next_file(None)


main()
