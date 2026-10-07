"""One controller per launcher, including static mode and bounded recovery."""
import json
from pathlib import Path
import time

from .renderers.background_frames import BackgroundFrames
from .settings import atomic_json, load
from .timeline import frame_at


def run(owner, runtime: Path, address: str, config_path: Path, frames: Path, mode: str) -> None:
    config = load(config_path)
    renderer = BackgroundFrames(address)
    started, last_image, failures = time.monotonic(), None, 0
    revision = None
    health = "ok"
    while owner.poll() is None:
        command_path = runtime / "command.json"
        if command_path.exists():
            try:
                command = json.loads(command_path.read_text())
                if command["revision"] != revision:
                    revision = command["revision"]
                    mode = "animated" if command["action"] in ("start", "restart") else "static"
                    if mode == "animated":
                        # Restart reloads only matching, prebuilt settings.
                        from .assets import validate
                        candidate = load(config_path)
                        validate(candidate, frames)
                        config = candidate
                        started = time.monotonic()
                    failures, health, last_image = 0, "ok", None
            except (ValueError, KeyError, OSError) as error:
                mode, health = "static", str(error)
        frame = frame_at(time.monotonic() - started, config)
        image = frames / ("static.png" if mode == "static" else
                          "blank.png" if frame.step == 0 else f"{frame.language}-{frame.step:03}.png")
        if image != last_image:
            try:
                renderer.show(image)
                last_image, failures = image, 0
            except Exception as error:
                failures += 1
                health = str(error)
                if failures >= 3:
                    mode = "static"
                    # One fallback attempt, then cease sending until explicitly restarted.
                    try:
                        renderer.show(frames / "static.png")
                    except Exception:
                        pass
                    last_image = frames / "static.png"
        atomic_json(runtime / "status.json", {"owner_pid": owner.pid, "mode": mode,
                    "phase": frame.phase if mode == "animated" else "static",
                    "language": frame.language, "health": health, "socket": address,
                    "updated_at": time.time()})
        # Child is checked regularly even during holds; only changing images are sent.
        time.sleep(1 / config["animation"]["fps"] if failures == 0 else 0.5)
