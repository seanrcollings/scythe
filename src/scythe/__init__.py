from pathlib import Path

project_root = Path(__file__).parent.parent.parent
config_file = Path("~/.config/scythe.conf").expanduser()
cache_file = Path("/tmp/scythe-cache")

from .cli import cli
