"""Optional real renderer test. Run under xvfb-run with Kitty/Fish on PATH."""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kedar_terminal.performance import monitor


def main():
    prefix = [sys.executable, str(ROOT / "scripts/kedar-terminal"), "--profile", str(ROOT / ".cache/profile"),
              "--frames", str(ROOT / ".cache/frames")]
    if "--baseline" in sys.argv:
        baseline_env = os.environ.copy()
        baseline_env["XDG_CONFIG_HOME"] = str(ROOT / ".cache/ptyxis-profile")
        baseline = subprocess.Popen(["dbus-run-session", "--", "ptyxis", "--standalone", "--", "bash"],
                                    env=baseline_env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                    start_new_session=True)
        try:
            time.sleep(3)
            if baseline.poll() is not None:
                raise RuntimeError(f"Ptyxis failed: {baseline.stderr.read().decode()}")
            default = monitor([baseline.pid], 12, 0.5, "ptyxis-default-settings-xvfb", ROOT / "reports/smoke-default")
            print(json.dumps(default, indent=2))
        finally:
            os.killpg(baseline.pid, signal.SIGTERM)
            baseline.wait(timeout=10)
    runtime = None
    child = subprocess.Popen(prefix + ["launch", "--", "fish"], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            candidates = sorted((ROOT / ".cache/runtime").glob("kedar-*/instance.json"))
            if candidates:
                runtime = candidates[-1].parent
                break
            if child.poll() is not None:
                raise RuntimeError(f"Kitty failed: {child.communicate()}")
            time.sleep(0.1)
        if runtime is None:
            raise RuntimeError("No owned socket found")
        def status():
            return json.loads((runtime / "status.json").read_text())
        def wait_mode(mode):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    value = status()
                    if value["mode"] == mode:
                        if value["health"] != "ok":
                            raise RuntimeError(value)
                        return value
                except FileNotFoundError:
                    pass
                time.sleep(0.1)
            raise RuntimeError(f"Mode did not become {mode}")
        value = wait_mode("animated")
        remote = ["kitten", "@", "--to", value["socket"]]
        subprocess.run(remote + ["send-text", "printf 'KEDAR_COMMAND_OK\\n'\r"], check=True)
        time.sleep(0.5)
        output = subprocess.check_output(remote + ["get-text"], text=True)
        if "KEDAR_COMMAND_OK" not in [line.strip() for line in output.splitlines()]:
            raise RuntimeError("Interactive shell did not execute test command")
        for action, mode in (("stop", "static"), ("start", "animated"), ("restart", "animated"), ("static", "static")):
            subprocess.run(prefix + ["animation", action, "--runtime", str(runtime)], check=True)
            wait_mode(mode)
        static = monitor([child.pid], 12, 0.5, "kitty-static-xvfb", ROOT / "reports/smoke-static")
        subprocess.run(prefix + ["animation", "start", "--runtime", str(runtime)], check=True)
        wait_mode("animated")
        animated = monitor([child.pid], 12, 0.5, "kitty-animated-xvfb", ROOT / "reports/smoke-animated")
        wait_mode("animated")
        subprocess.run(remote + ["close-window", "--match", "all"], check=True)
        child.wait(timeout=10)
        if child.returncode != 0:
            raise RuntimeError(child.stderr.read())
        if runtime.exists():
            raise RuntimeError("Runtime directory leaked")
        print(json.dumps({"result": "PASS", "static": static, "animated": animated}, indent=2))
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
