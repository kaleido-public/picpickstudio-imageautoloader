#!/usr/bin/env python3.10

import click
from pathlib import Path
import re
import marshmallow.exceptions
import yaml
import multiprocessing

from picpickstudio_imageautoloader.src.config import AppConfig
from picpickstudio_imageautoloader.src.window_watcher import WindowWatcher
from picpickstudio_imageautoloader.src.dir_watcher import DirWatcher


current_img_lock = multiprocessing.Lock()
current_img: str | None = None


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
        title_regex=re.compile(config_obj.window_title_regex),
        on_change=on_window_change,
    )
    dir_watcher = DirWatcher(
        use_polling=config_obj.use_polling,
        on_new_file=on_new_file,
        filename_regex=re.compile(config_obj.filename_regex),
        path=Path(config_obj.watch_dirpath),
    )

    current_img = None

    window_watcher.start()
    dir_watcher.start()


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
    print(file)
    with current_img_lock:
        global current_img
        current_img = file.name


def on_window_change() -> None:
    print("Window changed")
    with current_img_lock:
        global current_img
        current_img = None


main()
