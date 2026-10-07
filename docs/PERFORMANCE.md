# Measuring performance overhead

Keep the same resolution, window size, font size, workload, tab count, power
mode and compositor settings for each run. Measure three cases: default
terminal, Kedar static, Kedar animated. Repeat each at least three times,
alternating order. Let windows settle before sampling. Do not include frame
generation or installation in the runtime measurement.

## CPU and memory

Find the default terminal's actual process roots:

```bash
ps -eo pid,ppid,comm,args | rg 'ptyxis|gnome-terminal|kitty'
```

Ptyxis may use a separate backend process. Include both its UI and backend PIDs
with repeated `--pid` options if neither owns the other. Do not sample only
the shell PID and call that terminal memory. Run the sampler from a separate
terminal to keep its own work out of the measured tree.

```bash
python3 scripts/kedar-terminal monitor --pid DEFAULT_PID --label default --seconds 60 --output reports/default
```

Run the managed launch in a measuring terminal. `$!` below is the launcher PID;
sampling its tree includes the animation controller, Kitty, shell, and waited
frame-transfer helpers. Use the same tree scope for static and animated cases.

```bash
python3 scripts/kedar-terminal launch --mode static &
kedar_static_pid=$!
python3 scripts/kedar-terminal monitor --pid "$kedar_static_pid" --label static --seconds 60 --output reports/static
# Close the static Kitty window before measuring the animated case.

python3 scripts/kedar-terminal launch --mode animated &
kedar_animated_pid=$!
python3 scripts/kedar-terminal monitor --pid "$kedar_animated_pid" --label animated --seconds 60 --output reports/animated
python3 scripts/kedar-terminal compare reports/default.json reports/static.json reports/animated.json
```

Each monitor command writes a time series CSV and summary JSON. Reports include
mean/peak CPU, mean/peak RSS, first/last RSS, process counts, duration and host
metadata. CPU is percent of **one logical core**, so multithreaded workloads
can exceed 100%. Child CPU reaped by a parent is included to account for short
frame-transfer helpers. RSS sums shared pages more than once; it excludes VRAM,
GPU activity and the compositor. Escaped processes, short-lived RSS peaks, or
unreaped child CPU can escape attribution. Early root termination is recorded.

Comparison reports absolute CPU percentage-point and RSS MiB differences from
the first report. These are resource overheads, not a percentage loss of
terminal speed. Idle and active-command measurements answer different questions.

## Shell startup

```bash
python3 scripts/kedar-terminal benchmark-shell --shell /bin/bash --runs 20 --output reports/bash-startup.json
python3 scripts/kedar-terminal benchmark-shell --shell fish --custom --runs 20 --output reports/fish-startup.json
```

Each run uses a PTY and executes a readiness marker after interactive shell
initialization. The first warmup is discarded. Median and p95 measure shell
startup through first command execution, **not** the GUI's time-to-visible.
These commands may run existing interactive startup hooks. Use the actual
default shell if it differs from Bash.

## Desktop acceptance

Record Kitty/Fish versions, resolution, monitor scale and GPU alongside reports.
Check command typing, suggestion acceptance, npm/path/Git completion, selection,
copy/paste, scrollback, `clear`, resize, tabs/panes, `less`, Vim and tmux. Watch at
least ten complete bilingual cycles, and run a 10-minute monitor to inspect
memory growth. Inspect GPU activity/power using hardware-specific tools when
available; CPU/RSS alone cannot establish GPU or battery cost.

Proposed targets from the README: animation adds no more than 200 ms to startup,
average CPU below 10% of one core, controller RSS below 128 MiB, and no noticeable
typing delay. Our tree report includes Kitty and Fish, so it cannot alone verify
the **controller-only** RSS target. These are targets, not claimed results.

Lower `fps`, `steps`, or frame dimensions if resource use is high, then rebuild.
Static mode is an immediate way to measure or avoid animation overhead.

See [validation notes](VALIDATION.md) for the exploratory software-rendering
samples and their limitations. They do not establish desktop acceptance.
