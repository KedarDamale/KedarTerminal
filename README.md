# Kedar Ubuntu Terminal Theme

Configuration for the **existing Ubuntu terminal and Bash**, with a dark navy
background, teal accents, a KEDAR greeting and a compact username/path/Git prompt.
The previous Kitty/Fish/Starship application, Python package, animation controller,
tests and build tools have been removed.

```text
config/bash/kedar.bash       Bash greeting and prompt
config/native/kedar.palette Ptyxis colors
assets/landscape.png         Version-controlled wallpaper reference
LICENSE                     Apache-2.0
```

The theme has been applied to Kedar's default Ptyxis profile and `~/.bashrc`.
Open the normal Ubuntu Terminal again to load the greeting and prompt. The
settings persist across computer restarts. Bash tools, history, completion,
PATH and the login shell remain available.

Ptyxis supports a color palette and font preferences. This theme has a solid
navy background: it does **not** display an aurora image or animated lettering.
The saved landscape remains an artwork reference. There is no animation process
or separate terminal launcher.

## Updating the theme files

After editing the tracked configuration, copy it into the installed locations:

```bash
mkdir -p ~/.config/kedar-terminal/native
mkdir -p ~/.local/share/org.gnome.Ptyxis/palettes
cp config/bash/kedar.bash ~/.config/kedar-terminal/native/kedar.bash
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

## Removing the superseded packages

These packages were introduced by the earlier terminal setup. Removal requires
sudo authentication in your own terminal:

```bash
sudo apt-get purge -y kitty kitty-shell-integration kitty-terminfo kitty-doc \
  fish fish-common starship fonts-firacode fonts-font-awesome \
  fonts-material-design-icons-iconfont fonts-weather-icons xsel
```

The separate Kitty/Fish profile, generated frame cache, downloaded test packages,
and test toolchain have already been deleted. The default Ptyxis terminal and
Bash are retained.
