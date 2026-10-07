import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time

from .settings import atomic_json, load, xdg


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Kedar's isolated terminal and performance tools")
    checkout = Path(__file__).resolve().parents[2]
    default_root = checkout if (checkout / "assets/landscape.png").is_file() else Path(sys.prefix) / "share/kedar-terminal"
    p.add_argument("--root", type=Path, default=default_root, help="Repository root or installed data directory")
    p.add_argument("--profile", type=Path, default=xdg("CONFIG"), help="Isolated Kitty/Fish config directory")
    p.add_argument("--frames", type=Path, default=xdg("CACHE") / "frames")
    sub = p.add_subparsers(dest="operation", required=True)
    install = sub.add_parser("install", help="Sync changed profile files; preserve local edits and detect conflicts")
    install.add_argument("--force", action="store_true", help="Back up and replace locally edited regular files")
    restore = sub.add_parser("restore")
    restore.add_argument("backup", type=Path)
    build = sub.add_parser("build", help="Generate offline bilingual background frames")
    build.add_argument("--config", type=Path)
    build.add_argument("--if-needed", action="store_true", help="Reuse validated frames when inputs are unchanged")
    sub.add_parser("doctor")
    launch = sub.add_parser("launch")
    launch.add_argument("--mode", choices=["animated", "static"], default="animated")
    launch.add_argument("command", nargs=argparse.REMAINDER, help="Optional shell/program after --")
    control = sub.add_parser("animation")
    control.add_argument("action", choices=["start", "stop", "restart", "status", "static"])
    control.add_argument("--runtime", type=Path, default=os.environ.get("KEDAR_RUNTIME"))
    monitor = sub.add_parser("monitor")
    monitor.add_argument("--pid", type=int, action="append", required=True, help="Root PID; may repeat")
    monitor.add_argument("--seconds", type=float, default=60)
    monitor.add_argument("--interval", type=float, default=0.5)
    monitor.add_argument("--label", required=True)
    monitor.add_argument("--output", type=Path, required=True, help="Report path prefix")
    comparison = sub.add_parser("compare")
    comparison.add_argument("reports", nargs="+", type=Path, help="Baseline JSON first")
    benchmark = sub.add_parser("benchmark-shell")
    benchmark.add_argument("--shell", default=os.environ.get("SHELL", "/bin/bash"))
    benchmark.add_argument("--runs", type=int, default=20)
    benchmark.add_argument("--custom", action="store_true", help="Use the dedicated Fish profile")
    benchmark.add_argument("--output", type=Path)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    args.root, args.profile, args.frames = (p.expanduser().resolve() for p in (args.root, args.profile, args.frames))
    try:
        op = args.operation
        if op == "install":
            from .install import install
            backup = install(args.root, args.profile, force=args.force)
            print(f"Profile: {args.profile}\nBackup: {backup or 'none (no existing files replaced)'}")
        elif op == "restore":
            from .install import restore
            print(f"Saved replaced profile: {restore(args.backup.expanduser().resolve(), args.profile)}")
        elif op == "build":
            from .assets import build
            config_path = args.config or args.profile / "animation.toml"
            result = build(load(config_path), args.root / "assets/landscape.png", args.frames, if_needed=args.if_needed)
            print(f"Frames ready: {len(result['files'])} PNGs in {args.frames}")
        elif op == "launch":
            from .assets import validate
            from .launcher import launch
            animation_valid = True
            try:
                validate(load(args.profile / "animation.toml"), args.frames)
            except (OSError, ValueError, KeyError) as error:
                print(f"Static fallback: {error}. Run install/build to repair animation.", file=sys.stderr)
                animation_valid = False
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            return launch(args.profile, args.frames, args.mode, command,
                          args.root / "assets/landscape.png", animation_valid)
        elif op == "animation":
            if args.runtime is None:
                raise ValueError("Run inside managed Kitty or supply --runtime from launcher output")
            runtime = Path(args.runtime)
            instance = json.loads((runtime / "instance.json").read_text())
            os.kill(instance["pid"], 0)
            if args.action == "status":
                print((runtime / "status.json").read_text())
            else:
                atomic_json(runtime / "command.json", {"action": args.action, "revision": time.time_ns()})
                print(f"Requested {args.action}")
        elif op == "monitor":
            from .performance import monitor
            print(json.dumps(monitor(args.pid, args.seconds, args.interval, args.label, args.output), indent=2))
        elif op == "compare":
            from .performance import compare
            print(compare(args.reports))
        elif op == "benchmark-shell":
            from .performance import shell_startup
            env = os.environ.copy()
            if args.custom:
                env.update({"XDG_CONFIG_HOME": str(args.profile), "STARSHIP_CONFIG": str(args.profile / "starship.toml")})
            result = shell_startup(args.shell, args.runs, env)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                atomic_json(args.output, result)
            print(json.dumps(result, indent=2))
        elif op == "doctor":
            from PIL import features
            from .assets import validate, devanagari_font
            result = {binary: shutil.which(binary) for binary in ("kitty", "fish", "starship", "fc-match")}
            result["raqm"] = features.check_feature("raqm")
            for name, fn in (("settings", lambda: load(args.profile / "animation.toml")),
                             ("font", lambda: str(devanagari_font(load(args.profile / "animation.toml")))),
                             ("frames", lambda: validate(load(args.profile / "animation.toml"), args.frames)["dimensions"])):
                try:
                    result[name] = fn()
                except (OSError, ValueError) as error:
                    result[name] = f"ERROR: {error}"
            print(json.dumps(result, indent=2))
            return int(not all(result[b] for b in ("kitty", "fish", "starship", "raqm")) or any(
                isinstance(v, str) and v.startswith("ERROR:") for v in result.values()))
    except (OSError, ValueError, KeyError) as error:
        print(f"kedar-terminal: {error}", file=sys.stderr)
        return 1
    return 0
