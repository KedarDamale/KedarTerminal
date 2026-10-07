from pathlib import Path
import hashlib
import json
import math
import os
import tomllib


def xdg(kind: str) -> Path:
    defaults = {"CONFIG": ".config", "CACHE": ".cache", "DATA": ".local/share"}
    return Path(os.environ.get(f"XDG_{kind}_HOME", Path.home() / defaults[kind])) / "kedar-terminal"


def load(path: Path) -> dict:
    with path.open("rb") as stream:
        value = tomllib.load(stream)
    a, p = value["animation"], value["appearance"]
    for key, low, high in [("fps", 1, 30), ("steps", 2, 60)]:
        if type(a[key]) is not int or not low <= a[key] <= high:
            raise ValueError(f"{key} must be an integer in {low}..{high}")
    for key in ("write_on_seconds", "hold_seconds", "write_off_seconds", "gap_seconds"):
        if type(a[key]) not in (int, float) or not math.isfinite(a[key]) or not 0.05 <= a[key] <= 60:
            raise ValueError(f"{key} must be 0.05..60 seconds")
    for key in ("width", "height"):
        if type(p[key]) is not int or not 320 <= p[key] <= 2560:
            raise ValueError(f"{key} must be an integer in 320..2560")
    for key in ("name_x", "name_y", "name_width", "name_height", "name_opacity"):
        if type(p[key]) not in (int, float) or not math.isfinite(p[key]) or not 0 <= p[key] <= 1:
            raise ValueError(f"{key} must be between 0 and 1")
    if min(p["name_width"], p["name_height"]) <= 0:
        raise ValueError("Name dimensions must be positive")
    if p["name_x"] + p["name_width"] > 1 or p["name_y"] + p["name_height"] > 1:
        raise ValueError("Name region must fit inside the landscape")
    return value


def fingerprint(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)
