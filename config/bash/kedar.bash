# Sourced once from ~/.bashrc; all existing Bash tools and completion stay loaded.
[[ $- == *i* ]] || return
[[ ${KEDAR_BASH_LOADED:-} == 1 ]] && return
KEDAR_BASH_LOADED=1

_kedar_git_branch() {
    command -v git >/dev/null 2>&1 || return
    local branch
    branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null) || return
    printf ' › %s' "$branch"
}

if [[ ${TERM:-dumb} != dumb ]]; then
    PS1='\[\e[1;36m\]\u\[\e[0;90m\] › \[\e[1;34m\]\w\[\e[0;90m\]$(_kedar_git_branch)\[\e[0m\]\n❯ '
    if [[ -t 1 ]]; then
        printf '\033[1;36m'
        printf '█▄▀ █▀▀ █▀▄ ▄▀█ █▀█\n█ █ ██▄ █▄▀ █▀█ █▀▄\n'
        printf '\033[1;37mWelcome back, \033[1;36mKedar.\033[0m\n'
        printf '\033[90m%s\033[0m\n\n' "$(date '+%A, %d %B · %H:%M')"
    fi
fi

function kedar-header {
    local script=~/.config/kedar-terminal/native/header.py
    local action=${1:-status}
    local owner=$BASHPID
    [[ -f $script ]] || return
    case $action in
        start)
            { python3 "$script" "$owner" </dev/null >/dev/null 2>&1 &
              disown "$!"; } 2>/dev/null
            ;;
        stop|status) python3 "$script" "$action" ;;
        *) printf 'Usage: kedar-header start|stop|status\n' ;;
    esac
}
if [[ ${KEDAR_HEADER_ANIMATION:-1} == 1 && -t 0 && -t 1 && ${TERM:-dumb} != dumb && ! ${SSH_CONNECTION:-} ]]; then
    kedar-header start
fi

if declare -F ble-attach >/dev/null; then
    ble-attach
fi
