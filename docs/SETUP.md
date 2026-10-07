# Setup and usage

This is a separate Kitty + Fish profile. The installer writes only
`$XDG_CONFIG_HOME/kedar-terminal` (normally `~/.config/kedar-terminal`).
Your existing Bash, Fish, Kitty and Ptyxis configuration is not overwritten,
and your login shell is not changed. PATH is inherited from the launcher.

Run these commands from the repository in Bash:

```bash
sudo apt update
sudo apt install kitty fish starship fonts-firacode fonts-noto-core python3-pil fontconfig
python3 scripts/kedar-terminal install
python3 scripts/kedar-terminal build
python3 scripts/kedar-terminal doctor
python3 scripts/kedar-terminal launch
```

Requires Python 3.11+ and Pillow with RAQM. If your Ubuntu version does not
package Starship, follow its [official installation guide](https://starship.rs/guide/).
The bundled Fish prompt works while Starship is absent. Installation does not
download anything; once dependencies and assets are prepared, playback is offline.

For a virtual environment or installed CLI:

```bash
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/kedar-terminal install
.venv/bin/kedar-terminal build
.venv/bin/kedar-terminal launch
```

Configuration and the landscape are included in the Python distribution.
`python3 scripts/kedar-terminal` is also usable directly with distro Pillow.

## Settings and controls

Edit `~/.config/kedar-terminal/animation.toml`, then close active managed
windows, rebuild frames, and launch again. The installed settings are copies;
changing `config/` in the checkout requires another `install`.
Position and scale use normalized coordinates. Both names are shaped once,
then revealed from left to right and erased from right to left. The timing
loop uses a monotonic clock and skips late frames. Default is 12 fps during
changing phases. Hold and gap phases do not resend identical backgrounds.
There is one controller per launched Kitty process, shared by tabs and panes.

Inside a managed terminal, run:

```bash
python3 /absolute/path/to/KedarTerminal/scripts/kedar-terminal animation status
python3 /absolute/path/to/KedarTerminal/scripts/kedar-terminal animation stop
python3 /absolute/path/to/KedarTerminal/scripts/kedar-terminal animation start
python3 /absolute/path/to/KedarTerminal/scripts/kedar-terminal animation restart
python3 /absolute/path/to/KedarTerminal/scripts/kedar-terminal animation static
```

`stop` and `static` retain the static English artwork; `start` and `restart`
begin with English. `restart` reloads settings only if their cached frames match.
From another terminal add `--runtime /path/printed/by/launcher` after the action.
The launcher prints its Kitty PID and private runtime directory. Closing Kitty
stops its controller and removes that runtime directory. Missing frames or bad
settings retain a static terminal; a failed control channel gets three retries
and one static fallback attempt. Diagnostic messages never enter shell output.
Use static mode for full-screen programs whenever decoration distracts you.

Shortcuts: Ctrl+Shift+T adds a tab; Ctrl+Shift+Enter splits a pane;
Ctrl+Shift+Left/Right switches tabs; Ctrl+Shift+F toggles full-screen.
Fish supplies inline suggestions and Tab completions. Right arrow accepts a
suggestion. Optional installed zoxide is initialized automatically.

## Backup and restore

Reinstalling backs up the dedicated profile to a timestamped sibling. The
installer prints its exact location. Restore with:

```bash
python3 scripts/kedar-terminal restore ~/.config/kedar-terminal.backup-TIMESTAMP
```

The replaced profile is kept as a `before-restore` sibling. Close managed
windows before installing, restoring, or rebuilding cached frames.

## Checkout-local trial

To keep all configuration and cached output within this repository:

```bash
python3 scripts/kedar-terminal --profile .cache/profile --frames .cache/frames install
python3 scripts/kedar-terminal --profile .cache/profile --frames .cache/frames build
python3 scripts/kedar-terminal --profile .cache/profile --frames .cache/frames launch
```

`assets/landscape.png` is version controlled. The generated frame cache and
personal measurement files are ignored. The English treatment is a custom
block design inspired by the reference; Marathi is shaped with your installed
Noto font. Final visual approval and desktop interaction checks remain necessary.

## Architecture and limits

The background adapter uses Kitty's documented
[`set-background-image`](https://sw.kovidgoyal.net/kitty/remote-control/#kitten-set-background-image)
over a private Unix socket. `--all` targets only OS windows in that managed
instance. [`socket-only`](https://sw.kovidgoyal.net/kitty/conf/#opt-kitty.allow_remote_control)
disables control through terminal text. Socket discovery handles Kitty's PID
suffix. The controller never reads input, clears the screen or prints animation
characters. A new OS window joins the next changing frame; existing tabs share
the current background. Frames are transferred on demand, without preloading
the whole animation into VRAM.

GPU shaders, automatic focus/battery pause, and pen-stroke animation are not
implemented. Automatic alternate-screen detection is not implemented. Fish's
default completion remains enabled; tool-specific npm completions depend on
the installed Fish version and project. Bash functions such as nvm are not
Fish functions; inherited PATH works, but switching Node versions within Fish
needs your preferred Fish-compatible integration.

Run `make test` and `make check` for automated checks. The original requirements
remain in the root README; checked code is not a claim that the manual Ubuntu
acceptance checklist has passed.
