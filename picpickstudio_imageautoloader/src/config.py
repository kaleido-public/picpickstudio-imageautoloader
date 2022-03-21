from dataclasses import dataclass
import marshmallow_dataclass
import yaml


@dataclass
class AppConfig:
    window_title_regex: str
    window_title_regex_case_sensitive: bool
    use_polling: bool
    polling_frequency_ms: int
    filename_regex: str
    filename_regex_case_sensitive: bool
    watch_dirpath: str

    @staticmethod
    def default_config() -> "AppConfig":
        return AppConfig(
            window_title_regex="Remote Live View window",
            window_title_regex_case_sensitive=False,
            use_polling=True,
            polling_frequency_ms=1000,
            filename_regex=".*\.jpg",
            filename_regex_case_sensitive=False,
            watch_dirpath="./",
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
