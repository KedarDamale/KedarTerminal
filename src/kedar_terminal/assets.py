"""Offline frame preparation, with full-word RAQM shaping for Devanagari."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import unicodedata

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFont, features

from .settings import atomic_json, fingerprint

# Sculpted 5x7 block lettering instead of an ordinary bold font.
LETTERS = {
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
}


def devanagari_font(config: dict) -> Path:
    explicit = config["appearance"]["marathi_font"]
    if explicit:
        path = Path(explicit).expanduser()
    else:
        result = subprocess.run(["fc-match", "Noto Sans Devanagari", "-f", "%{file}"],
                                check=True, capture_output=True, text=True)
        path = Path(result.stdout)
        if "Devanagari" not in path.name:
            raise ValueError("Install fonts-noto-core or configure marathi_font")
    if not path.is_file():
        raise ValueError(f"Missing Devanagari font: {path}")
    if not features.check_feature("raqm"):
        raise ValueError("Pillow must have RAQM for correctly shaped केदार")
    return path


def english_mask() -> Image.Image:
    mask = Image.new("L", (29 * 20, 7 * 20))
    draw = ImageDraw.Draw(mask)
    for i, letter in enumerate("KEDAR"):
        for y, row in enumerate(LETTERS[letter]):
            for x, cell in enumerate(row):
                if cell == "1":
                    left, top = (i * 6 + x) * 20, y * 20
                    draw.rectangle((left + 1, top + 1, left + 17, top + 17), fill=255)
                    draw.line((left + 4, top + 5, left + 4, top + 15), fill=145, width=2)
    return mask


def marathi_mask(font: Path) -> Image.Image:
    face = ImageFont.truetype(str(font), 230, layout_engine=ImageFont.Layout.RAQM)
    text = unicodedata.normalize("NFC", "केदार")
    bounds = face.getbbox(text, language="mr")
    mask = Image.new("L", (bounds[2] - bounds[0] + 4, bounds[3] - bounds[1] + 4))
    ImageDraw.Draw(mask).text((2 - bounds[0], 2 - bounds[1]), text, font=face,
                             fill=255, language="mr")
    # Subtle grid etching after shaping; never split combining characters.
    grid = Image.new("L", mask.size, 255)
    draw = ImageDraw.Draw(grid)
    for x in range(0, mask.width, 16):
        draw.line((x, 0, x, mask.height), fill=160)
    return ImageChops.multiply(mask, grid)


def build(config: dict, landscape: Path, output: Path) -> dict:
    font = devanagari_font(config)
    p, a = config["appearance"], config["animation"]
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="frames-", dir=output.parent))
    try:
        base = Image.open(landscape).convert("RGB").resize((p["width"], p["height"]), Image.Resampling.LANCZOS)
        base.save(staging / "blank.png")
        color = ImageColor.getrgb(p["foreground"])
        for language, mask in (("en", english_mask()), ("mr", marathi_mask(font))):
            w, h = int(base.width * p["name_width"]), int(base.height * p["name_height"])
            mask.thumbnail((w, h), Image.Resampling.LANCZOS)
            x = int(base.width * p["name_x"]) + (w - mask.width) // 2
            y = int(base.height * p["name_y"]) + (h - mask.height) // 2
            mask = mask.point(lambda v: round(v * p["name_opacity"]))
            for step in range(1, a["steps"] + 1):
                shown = mask.copy()
                cut = math.ceil(mask.width * step / a["steps"])
                ImageDraw.Draw(shown).rectangle((cut, 0, mask.width, mask.height), fill=0)
                frame = base.copy()
                # Offset dim shadow recalls the reference's sculpted lettering.
                frame.paste((13, 95, 104), (x + 6, y + 8), shown)
                frame.paste(color, (x, y), shown)
                frame.save(staging / f"{language}-{step:03}.png")
        shutil.copy2(staging / f"en-{a['steps']:03}.png", staging / "static.png")
        manifest = {"schema": 1, "config_hash": fingerprint(config),
                    "landscape_sha256": hashlib.sha256(landscape.read_bytes()).hexdigest(),
                    "font": str(font), "font_sha256": hashlib.sha256(font.read_bytes()).hexdigest(),
                    "dimensions": [base.width, base.height], "steps": a["steps"],
                    "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                              for f in sorted(staging.glob("*.png"))}}
        atomic_json(staging / "manifest.json", manifest)
        # Cache replacement is explicit and confined to this tool's frame directory.
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
        return manifest
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def validate(config: dict, frames: Path) -> dict:
    manifest = json.loads((frames / "manifest.json").read_text())
    if manifest["config_hash"] != fingerprint(config):
        raise ValueError("Animation settings changed; run build before launch")
    for name, expected in manifest["files"].items():
        path = frames / name
        if path.parent != frames or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Invalid cached frame: {name}; run build")
    return manifest
