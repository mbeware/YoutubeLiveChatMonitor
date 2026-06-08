from pathlib import Path
import tomlkit
from typing import Any


class ConfigObject(dict):
    """Converts dict keys to attributes."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, val):
        self[name] = val


def config2object(config):
    if isinstance(config, dict):
        result = ConfigObject()
        for key, value in config.items():
            result[key] = config2object(value)
        return result
    return config



def readconfig(config_filename: str):
    config_path = Path(config_filename)

    if not config_path.exists():
        raise FileNotFoundError(f"No config file: {config_path}")

    with config_path.open("rb") as f:
        config_dict = tomlkit.load(f)

    config = config2object(config_dict)
    return config


