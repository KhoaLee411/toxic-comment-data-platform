import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_cfg(cfg_path: str) -> dict:
    load_dotenv()
    raw = Path(cfg_path).read_text()
    expanded = os.path.expandvars(raw)
    return yaml.safe_load(expanded)
