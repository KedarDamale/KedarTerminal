"""Launch an isolated Fish profile and supervise only this Kitty process."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

from .controller import run
from .settings import atomic_json, xdg


def launch(profile: Path, frames: Path, mode: str, command: list[str], landscape: Path,
           animation_valid: bool = True) -> int:
    if not shutil.which("kitty") or not shutil.which("fish"):
        raise ValueError("Install kitty and fish first (see docs/SETUP.md)")
    runtime_parent = Path(os.environ.get("XDG_RUNTIME_DIR", xdg("CACHE") / "runtime"))
    runtime_parent.mkdir(parents=True, exist_ok=True)
    runtime = Path(tempfile.mkdtemp(prefix="kedar-", dir=runtime_parent))
    runtime.chmod(0o700)
    env = os.environ.copy()
    env.update({"XDG_CONFIG_HOME": str(profile), "STARSHIP_CONFIG": str(profile / "starship.toml"),
                "KEDAR_RUNTIME": str(runtime)})
    config = runtime / "kitty.conf"
    # Paths in Kitty's config need no shell quoting; reject newlines from path input.
    for path in (profile, frames):
        if "\n" in str(path):
            raise ValueError("Configuration paths cannot contain newlines")
    background = frames / "static.png" if (frames / "static.png").is_file() else landscape
    include = f"include {profile / 'kitty.conf'}\n" if (profile / "kitty.conf").is_file() else ""
    config.write_text(include + f"background_image {background}\nallow_remote_control socket-only\n")
    terminal = None
    old_handlers = {}
    try:
        terminal = subprocess.Popen(["kitty", "--config", str(config), "--listen-on",
                                    f"unix:{runtime}/kitty-{{kitty_pid}}.sock", *(command or ["fish"])], env=env)
        def stop(signum, frame):
            if terminal.poll() is None:
                terminal.terminate()
        for sig in (signal.SIGTERM, signal.SIGINT):
            old_handlers[sig] = signal.signal(sig, stop)
        deadline = time.monotonic() + 10
        sockets = []
        while terminal.poll() is None and time.monotonic() < deadline:
            sockets = list(runtime.glob("kitty-*.sock"))
            if sockets:
                break
            time.sleep(0.05)
        if terminal.poll() is None and sockets:
            address = f"unix:{sockets[0]}"
            atomic_json(runtime / "instance.json", {"pid": terminal.pid, "socket": address})
            print(f"Managed Kitty PID: {terminal.pid}; controls: --runtime {runtime}", flush=True)
            if animation_valid:
                run(terminal, runtime, address, profile / "animation.toml", frames, mode)
        elif terminal.poll() is None:
            print("Remote control unavailable; retaining usable static terminal.", flush=True)
        return terminal.wait()
    finally:
        if terminal and terminal.poll() is None:
            terminal.terminate()
            try:
                terminal.wait(timeout=5)
            except subprocess.TimeoutExpired:
                terminal.kill()
                terminal.wait()
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        shutil.rmtree(runtime)
