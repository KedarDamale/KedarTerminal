"""Backup/restore only the dedicated profile, leaving default terminal intact."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess


def install(root: Path, target: Path) -> Path | None:
    if shutil.which("fish"):
        for source in (root / "config/fish").rglob("*.fish"):
            subprocess.run(["fish", "--no-config", "--no-execute", str(source)], check=True)
    backup = None
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup = target.with_name(target.name + ".backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        shutil.copytree(target, backup)
    shutil.copytree(root / "config", target, dirs_exist_ok=True)
    return backup


def restore(backup: Path, target: Path) -> Path | None:
    if not backup.is_dir() or not (backup / "kitty.conf").is_file():
        raise ValueError("Backup must contain kitty.conf")
    if backup.resolve() == target.resolve() or target.resolve() in backup.resolve().parents:
        raise ValueError("Backup must be outside the target directory")
    saved = None
    if target.exists():
        saved = target.with_name(target.name + ".before-restore-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        target.rename(saved)
    shutil.copytree(backup, target)
    return saved
