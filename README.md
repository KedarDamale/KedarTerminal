# Kedar Ubuntu Terminal Theme

Configuration for the **existing Ubuntu terminal and Bash**, with a dark navy
background, teal accents, a KEDAR greeting and a compact username/path/Git prompt.
The previous Kitty/Fish/Starship application, Python package, animation controller,
tests and build tools have been removed.

```text
config/bash/kedar.bash       Bash greeting, prompt and editor attachment
config/bash/ble-start.bash   Load Bash suggestions before other startup settings
config/bash/ble-init.bash    Suggestion and completion settings
config/bash/header.py       Per-terminal KEDAR/केदार title animation
config/native/kedar.palette Ptyxis colors
assets/landscape.png         Version-controlled wallpaper reference
LICENSE                     Apache-2.0
```

The theme has been applied to Kedar's default Ptyxis profile and `~/.bashrc`.
Open the normal Ubuntu Terminal again to load the greeting and prompt. The
settings persist across computer restarts. Bash tools, history, completion,
PATH and the login shell remain available.

Ptyxis supports a color palette and font preferences. This theme has a solid
navy background: it does **not** display an aurora image or animate lettering
behind command text.
The saved landscape remains an artwork reference. A small title animator runs
per terminal; it only changes the tab/window title. Ptyxis's settings do not
support moving gradients or animated lines behind the command text.

## Animated header

The header progressively writes **KEDAR**, holds it, erases it, then repeats with
**केदार**. Marathi letter groups include their vowel marks. A loop lasts ten
seconds. Command text, suggestions, selections and scrollback are not repainted.
One process owns each terminal's title; duplicate starts are ignored. It stops
when the owning Bash process exits. Title updates use the standard OSC 2 sequence.

Open a new normal terminal, or run `exec bash`, to load it. Controls:

```bash
kedar-header status
kedar-header stop
kedar-header start
```

Stopping leaves a static `KEDAR · केदार` title. For future sessions, set
`KEDAR_HEADER_ANIMATION=0` before sourcing the theme in `.bashrc`. SSH sessions
skip the animation. Native terminal/shell title updates may briefly replace
the name; the animator reasserts its title within half a second.

## Suggestions and completion

The existing Bash terminal now loads [ble.sh](https://github.com/akinomyoga/ble.sh)
for dim inline suggestions, syntax highlighting and a Tab completion menu.
`bash-completion` was already installed. Suggestions come from shell history and
available completions; no cloud service is used.

Open a new normal terminal after installation. Right Arrow accepts the suggested
suffix when the cursor is at the end of the line. Tab opens/completes commands,
paths and supported arguments; Tab/Shift+Tab navigate multiple candidates.
Ctrl+R searches history. Suggestions use a 250 ms delay.

ble.sh is installed at `~/.local/share/blesh`; no Fish, Kitty or Starship is
required. The Bash suggestion loader is a separate marked block at the start
of `.bashrc`, and the theme attaches the editor at the end. The installed build
is `0.4.0-nightly+d81fd54`. The original startup file before this change is saved
under `native/backups/completion-20261007T143532/`.

To disable suggestions, remove the marked loader block:

```bash
sed -i '/^# >>> Kedar Bash suggestions >>>$/,/^# <<< Kedar Bash suggestions <<<$/d' ~/.bashrc
```

Then open a new terminal. The palette and prompt remain configured.

## Updating the theme files

After editing the tracked configuration, copy it into the installed locations:

```bash
mkdir -p ~/.config/kedar-terminal/native
mkdir -p ~/.local/share/org.gnome.Ptyxis/palettes
cp config/bash/kedar.bash ~/.config/kedar-terminal/native/kedar.bash
cp config/bash/ble-start.bash ~/.config/kedar-terminal/native/ble-start.bash
cp config/bash/ble-init.bash ~/.config/kedar-terminal/native/ble-init.bash
cp config/bash/header.py ~/.config/kedar-terminal/native/header.py
cp config/native/kedar.palette ~/.local/share/org.gnome.Ptyxis/palettes/kedar.palette
```

Open a new normal terminal. Restart Ptyxis if the palette edit does not refresh.
Bash syntax can be checked with `bash -n config/bash/kedar.bash`.

The existing `.bashrc` has one marked block sourcing the installed Bash theme.
Do not add duplicate source lines. Only `~/.bashrc` and the existing default
terminal profile are customized; there is no need for `make launch`.

## Backup

Original settings and startup-file contents are saved under:

```text
~/.config/kedar-terminal/native/backups/20261007T140230591087/
```

`before.json` contains the exact original GSettings values and file contents.
`bashrc.before` is a readable copy of the original startup file.

To remove the Bash theme while retaining your other `.bashrc` edits:

```bash
sed -i '/^# >>> Kedar Terminal Bash theme >>>$/,/^# <<< Kedar Terminal Bash theme <<<$/d' ~/.bashrc
```

Restore individual terminal preferences from `before.json` using `gsettings set`.

## Superseded packages removed

These 12 packages introduced by the earlier setup have been purged, freeing
approximately 105 MB:

```bash
kitty, kitty-shell-integration, kitty-terminfo, kitty-doc,
fish, fish-common, starship, fonts-firacode, fonts-font-awesome,
fonts-material-design-icons-iconfont, fonts-weather-icons, xsel
```

The separate Kitty/Fish profile, generated frame cache, downloaded test packages,
and test toolchain have already been deleted. The default Ptyxis terminal and
Bash are retained.
