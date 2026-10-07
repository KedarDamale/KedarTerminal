"""A small, per-terminal title animator; never paints terminal content."""
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import sys
import time


def token(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return None if fields[0] in ("Z", "X") else fields[19]
    except (OSError, IndexError):
        return None


def title_at(elapsed):
    durations = (1.5, 2.0, 1.0, 0.5)
    position = elapsed % (2 * sum(durations))
    for clusters in (("K", "E", "D", "A", "R"), ("के", "दा", "र")):
        for phase, duration in enumerate(durations):
            if position < duration:
                fraction = position / duration
                count = (min(len(clusters), math.ceil(fraction * len(clusters))) if phase == 0 else
                         len(clusters) if phase == 1 else
                         max(0, math.ceil((1 - fraction) * len(clusters))) if phase == 2 else 0)
                word = "".join(clusters[:count]) or "·"
                return f"✦  {word}  ✦"
            position -= duration


def main():
    try:
        tty = os.open("/dev/tty", os.O_WRONLY | os.O_NOCTTY)
    except OSError:
        return 0
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", Path.home() / ".cache")) / "kedar-header"
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = runtime / f"tty-{os.fstat(tty).st_rdev}.json"
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode in ("stop", "status"):
        try:
            state = json.loads(path.read_text())
            live = token(state["pid"]) == state["token"]
        except (OSError, ValueError, KeyError):
            live, state = False, {}
        if mode == "stop" and live:
            os.kill(state["pid"], signal.SIGTERM)
            for _ in range(20):
                if not path.exists():
                    break
                time.sleep(0.05)
        elif mode == "status":
            print("Header animation: " + ("running" if live else "stopped"))
        os.close(tty)
        return 0
    owner = int(mode)
    owner_token = token(owner)
    if owner_token is None:
        os.close(tty)
        return 0
    with path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(tty)
            return 0
        state = {"pid": os.getpid(), "token": token(os.getpid()), "owner": owner}
        lock.seek(0)
        lock.truncate()
        json.dump(state, lock)
        lock.flush()
        running = True
        def stop(signum, frame):
            nonlocal running
            running = False
        for sig in (signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, stop)
        started, previous, sent_at = time.monotonic(), None, 0
        try:
            while running and token(owner) == owner_token:
                now = time.monotonic()
                title = title_at(now - started)
                # Reassert periodically because VTE shell integration also sets titles.
                if title != previous or now - sent_at >= 0.5:
                    os.write(tty, ("\x1b]2;" + title + "\x07").encode())
                    previous, sent_at = title, now
                time.sleep(0.1)
        except OSError:
            pass
        finally:
            try:
                os.write(tty, "\x1b]2;✦  KEDAR · केदार  ✦\x07".encode())
            except OSError:
                pass
            path.unlink(missing_ok=True)
            os.close(tty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
