import os
from pathlib import Path
import xdg

PROJECT_ROOT = Path(__file__).parent.parent

if os.getenv("SCYTHE_ENV") == "development":
    QUICKSTART_DATA = PROJECT_ROOT / "data" / "scythe-quickstart.json"
    STACK_DATA = PROJECT_ROOT / "data" / "scythe-stack.json"
else:
    QUICKSTART_DATA = xdg.xdg_data_home() / "scythe-quickstart.json"
    STACK_DATA = xdg.xdg_data_home() / "scythe-stack.json"
