import os
from pathlib import Path
import xdg

PROJECT_ROOT = Path(__file__).parent.parent

if os.getenv("SCYTHE_ENV") == "development":
    CONFIG_DIR = PROJECT_ROOT / "data"
    CACHE_DIR = CONFIG_DIR
    AUTOLOAD_DIR = CONFIG_DIR / "ext"
    QUICKSTART_DATA = CONFIG_DIR / "scythe-quickstart.json"
else:
    CONFIG_DIR = xdg.xdg_config_home() / "scythe"
    CACHE_DIR = xdg.xdg_cache_home()
    AUTOLOAD_DIR = xdg.xdg_data_home() / "scythe"
    QUICKSTART_DATA = xdg.xdg_data_home() / "scythe-quickstart.json"


CONFIG_FILE = CONFIG_DIR / "config.toml"
