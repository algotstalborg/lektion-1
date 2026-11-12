import json
from pathlib import Path

from config import (
    DATA_DIR,
    TASKS_FILE,
    CATEGORIES_FILE,
    SETTINGS_FILE,
    DEFAULT_CATEGORIES,
    DEFAULT_SETTINGS
)


def initialize_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    defaults = {
        TASKS_FILE: [],
        CATEGORIES_FILE: DEFAULT_CATEGORIES,
        SETTINGS_FILE: DEFAULT_SETTINGS
    }

    for path, default in defaults.items():
        if not path.exists():
            save_json(path, default)


def load_json(path, default=None):
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    temporary.replace(path)


def load_tasks():
    return load_json(TASKS_FILE, [])


def save_tasks(tasks):
    save_json(TASKS_FILE, tasks)


def load_categories():
    return load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES)


def save_categories(categories):
    save_json(CATEGORIES_FILE, categories)


def load_settings():
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)
