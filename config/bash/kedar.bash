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
