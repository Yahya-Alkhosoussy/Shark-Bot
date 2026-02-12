from pathlib import Path

import yaml

from utils.core import AppConfig


def load_config(CONFIG: Path):
    """
    Loads a .yaml or a .yml file.

    Args:
        CONFIG (PATH): The path of the config file.

    Returns:
        dict: a dictionary of the contents of the YAML file.
    """
    return yaml.safe_load(CONFIG.read_text(encoding="UTF-8")) or {}


def save_config(CONFIG: Path, cfg: AppConfig):
    """
    saves changed to a YAML file

    Args:
        CONFIG (Path): The path of the config file.
        cfg    (AppConfig): The dictionary to be saved into the YAML file.
    """
    temp = CONFIG.with_suffix(".tmp")
    temp.write_text(yaml.safe_dump(cfg.model_dump(), sort_keys=False, allow_unicode=True), encoding=("UTF-8"))
    temp.replace(CONFIG)


def read_config(CONFIG: Path):
    """
    Reads a YAML file.

    :param:
        CONFIG (Path): The path of the YAML file.

    Returns:
        dict: a dictionary of the contents of the YAML file.
    """
    with open(CONFIG, "r") as file:
        data: dict = yaml.full_load(file)

    return data
