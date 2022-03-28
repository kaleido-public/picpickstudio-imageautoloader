from dataclasses import dataclass
import marshmallow_dataclass
import yaml


@dataclass
class WindowWatcherConfig:
    interval: float
    title_regex: str
    tolerance: float

    @staticmethod
    def default() -> "WindowWatcherConfig":
        return WindowWatcherConfig(
            interval=1.0,
            title_regex=".*Remote Live View window.*",
            tolerance=0.05,
        )


@dataclass
class DirWatcherConfig:
    watch_dirpath: str
    filename_regex: str
    interval: float

    @staticmethod
    def default() -> "DirWatcherConfig":
        return DirWatcherConfig(
            interval=1.0,
            watch_dirpath="./",
            filename_regex=".*\.jpg",
        )


@dataclass
class ImagePreviewerConfig:
    interval: float

    @staticmethod
    def default() -> "ImagePreviewerConfig":
        return ImagePreviewerConfig(
            interval=1.0,
        )


@dataclass
class AppConfig:
    dir_watcher: DirWatcherConfig
    window_watcher: WindowWatcherConfig
    image_previewer: ImagePreviewerConfig

    @staticmethod
    def default() -> "AppConfig":
        return AppConfig(
            dir_watcher=DirWatcherConfig.default(),
            window_watcher=WindowWatcherConfig.default(),
            image_previewer=ImagePreviewerConfig.default(),
        )

    @staticmethod
    def from_yaml(content: str) -> "AppConfig":
        schema = marshmallow_dataclass.class_schema(AppConfig)()
        dic = yaml.safe_load(content)
        return schema.load(dic)

    def to_yaml(self) -> str:
        schema = marshmallow_dataclass.class_schema(AppConfig)()
        dic = schema.dump(self)
        return yaml.dump(dic)
