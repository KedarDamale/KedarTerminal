"""Linux /proc process-tree sampling and PTY shell-startup measurements."""
import csv
import json
import os
from pathlib import Path
import platform
import pty
import select
import statistics
import subprocess
import time

from .settings import atomic_json


def processes() -> dict:
    result = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            raw = path.read_text()
            fields = raw[raw.rfind(")") + 2:].split()
            result[int(path.parent.name)] = {"ppid": int(fields[1]), "ticks": sum(int(fields[i]) for i in (11, 12, 13, 14)),
                "start": int(fields[19]), "rss": int(fields[21]) * os.sysconf("SC_PAGE_SIZE")}
        except (OSError, ValueError, IndexError):
            continue
    return result


def tree(snapshot: dict, roots: list[int]) -> dict:
    owned = set(roots)
    while True:
        added = {pid for pid, value in snapshot.items() if value["ppid"] in owned} - owned
        if not added:
            return {pid: snapshot[pid] for pid in owned if pid in snapshot}
        owned.update(added)


def monitor(roots: list[int], seconds: float, interval: float, label: str, output: Path) -> dict:
    if seconds <= 0 or interval < 0.1:
        raise ValueError("Duration must be positive; interval must be at least 0.1 s")
    snapshot = processes()
    if any(pid not in snapshot for pid in roots):
        raise ValueError("A supplied root PID does not exist")
    identities = {pid: snapshot[pid]["start"] for pid in roots}
    previous = tree(snapshot, roots)
    started = last = time.monotonic()
    rows = []
    while time.monotonic() - started < seconds:
        time.sleep(min(interval, max(0, seconds - (time.monotonic() - started))))
        now = time.monotonic()
        snapshot = processes()
        # Never follow an unrelated process if a root PID was reused.
        active_roots = [pid for pid, birth in identities.items() if snapshot.get(pid, {}).get("start") == birth]
        current = tree(snapshot, active_roots)
        # Include waited-for children: frame-transfer helpers are short-lived.
        # Their totals migrate to the waiting parent's cutime/cstime after exit.
        ticks = max(0, sum(v["ticks"] for v in current.values()) - sum(v["ticks"] for v in previous.values()))
        cpu = ticks / os.sysconf("SC_CLK_TCK") / (now - last) * 100
        rows.append({"elapsed_s": round(now - started, 3), "cpu_percent_one_core": round(cpu, 3),
                     "rss_mib": round(sum(v["rss"] for v in current.values()) / 2**20, 3),
                     "processes": len(current), "root_alive": bool(active_roots)})
        previous, last = current, now
        if not active_roots:
            break
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(".csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    cpu, memory = [r["cpu_percent_one_core"] for r in rows], [r["rss_mib"] for r in rows]
    summary = {"label": label, "root_pids": roots, "duration_s": rows[-1]["elapsed_s"],
        "interval_s": interval, "samples": len(rows), "cpu_mean_percent": statistics.mean(cpu),
        "cpu_peak_percent": max(cpu), "rss_mean_mib": statistics.mean(memory), "rss_peak_mib": max(memory),
        "rss_first_mib": memory[0], "rss_last_mib": memory[-1], "platform": platform.platform(),
        "logical_cpus": os.cpu_count(), "all_roots_alive_at_end": all(pid in active_roots for pid in roots),
        "limitations": "RSS double-counts shared pages; excludes GPU VRAM and compositor. Waited child CPU is included, but escaped/unreaped processes and short-lived RSS peaks can be missed. CPU is percent of one logical core. Match workloads and window sizes."}
    atomic_json(output.with_suffix(".json"), summary)
    return summary


def compare(paths: list[Path]) -> str:
    reports = [json.loads(p.read_text()) for p in paths]
    base = reports[0]
    lines = ["| Profile | Mean CPU (one core %) | Mean RSS MiB | CPU change (points) | RSS change MiB |",
             "|---|---:|---:|---:|---:|"]
    for r in reports:
        lines.append(f"| {r['label']} | {r['cpu_mean_percent']:.2f} | {r['rss_mean_mib']:.2f} | "
                     f"{r['cpu_mean_percent'] - base['cpu_mean_percent']:+.2f} | "
                     f"{r['rss_mean_mib'] - base['rss_mean_mib']:+.2f} |")
    lines.append("\nResource overhead is not a measurement of typing latency or GPU performance.")
    return "\n".join(lines)


def shell_startup(shell: str, runs: int, env: dict | None = None) -> dict:
    if runs < 3:
        raise ValueError("Use at least three runs")
    samples = []
    # Each run has a PTY, so interactive startup paths actually execute.
    for _ in range(runs + 1):
        master, slave = pty.openpty()
        process = None
        try:
            start = time.perf_counter()
            process = subprocess.Popen([shell, "-ic", "printf '__KEDAR_READY__\\n'"],
                                       stdin=slave, stdout=slave, stderr=slave, env=env, start_new_session=True)
            os.close(slave)
            slave = -1
            data = b""
            deadline = time.monotonic() + 10
            while b"__KEDAR_READY__\r\n" not in data:
                if time.monotonic() >= deadline:
                    raise ValueError(f"{shell} startup timed out")
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError as error:
                        raise ValueError(f"{shell} exited before readiness") from error
                    if not chunk:
                        raise ValueError(f"{shell} exited before readiness")
                    data += chunk
            samples.append((time.perf_counter() - start) * 1000)
            process.wait(timeout=3)
        finally:
            os.close(master)
            if slave != -1:
                os.close(slave)
            if process and process.poll() is None:
                process.kill()
                process.wait()
    samples = samples[1:]
    ordered = sorted(samples)
    return {"shell": shell, "runs": runs, "median_ms": statistics.median(samples),
            "p95_ms": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], "samples_ms": samples,
            "scope": "PTY shell startup through command execution; excludes emulator/window/GPU startup; first warmup discarded"}
