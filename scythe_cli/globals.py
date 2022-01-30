from pathlib import Path
import xdg

_CONFIG = xdg.xdg_config_home()


PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
# CONFIG_DIR = _CONFIG / "scythe"
# CONFIG_FILE = CONFIG_DIR / "config.yaml"
CACHE_FILE: Path = Path("/tmp/scythe-cache")
