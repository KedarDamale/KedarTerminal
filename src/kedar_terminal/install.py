"""Backup/restore only the dedicated profile, leaving default terminal intact."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

from .settings import atomic_json


def install(root: Path, target: Path, force: bool = False) -> Path | None:
    if shutil.which("fish"):
        for source in (root / "config/fish").rglob("*.fish"):
            subprocess.run(["fish", "--no-config", "--no-execute", str(source)], check=True)
    state_path = target / ".kedar-install.json"
    previous = json.loads(state_path.read_text())["files"] if state_path.exists() else {}
    sources = {p.relative_to(root / "config").as_posix(): p
               for p in sorted((root / "config").rglob("*")) if p.is_file()}
    if not sources:
        raise ValueError("Repository configuration is missing")
    desired = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sources.items()}
    for name in previous:
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Invalid installed-file manifest")
    changes, removals, conflicts = [], [], []
    for name, digest in desired.items():
        destination = target / name
        current = hashlib.sha256(destination.read_bytes()).hexdigest() if destination.is_file() else None
        old = previous.get(name)
        if current == digest:
            continue
        if not force and old == digest:
            # Upstream did not change: keep this user's edits or deletion.
            continue
        if destination.is_symlink():
            conflicts.append(name + " (symlink)")
        elif force or current == old:
            changes.append(name)
        else:
            conflicts.append(name)
    for name, old in previous.items():
        if name in desired:
            continue
        destination = target / name
        if destination.is_file() and not destination.is_symlink() and hashlib.sha256(destination.read_bytes()).hexdigest() == old:
            removals.append(name)
    if conflicts:
        raise ValueError("Configuration conflicts: " + ", ".join(conflicts) +
                         ". Merge these files, or use install --force to back up and replace regular files. No files changed.")
    backup = None
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and (changes or removals):
        backup = target.with_name(target.name + ".backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        shutil.copytree(target, backup)
    target.mkdir(parents=True, exist_ok=True)
    for name in changes:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sources[name], destination)
    for name in removals:
        (target / name).unlink()
    state = {"schema": 1, "files": desired}
    if not state_path.exists() or json.loads(state_path.read_text()) != state:
        atomic_json(state_path, state)
    print(f"Profile sync: {len(changes)} changed, {len(removals)} removed; remaining files preserved")
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
