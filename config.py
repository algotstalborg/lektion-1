from pathlib import Path

APP_NAME = "Min Planerare"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

TASKS_FILE = DATA_DIR / "tasks.json"
CATEGORIES_FILE = DATA_DIR / "categories.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750

DEFAULT_CATEGORIES = [
    {"name": "Hemma", "color": "#4A90E2"},
    {"name": "Arbete", "color": "#9B59B6"},
    {"name": "Studier", "color": "#E67E22"},
    {"name": "Hälsa", "color": "#27AE60"},
    {"name": "Personligt", "color": "#E84393"},
]

DEFAULT_SETTINGS = {
    "theme": "light",
    "language": "sv",
    "week_start": "monday",
    "default_reminder": 30
}
