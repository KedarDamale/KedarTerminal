# Load before the rest of ~/.bashrc; the theme attaches it after prompt setup.
if [[ $- == *i* && -t 0 && -t 1 && ${TERM:-dumb} != dumb && ! ${BLE_VERSION-} ]]; then
    if [[ -f ~/.local/share/blesh/ble.sh ]]; then
        source -- ~/.local/share/blesh/ble.sh --attach=none \
            --rcfile ~/.config/kedar-terminal/native/ble-init.bash
    fi
fi
