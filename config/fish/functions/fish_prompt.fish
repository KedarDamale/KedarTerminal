# Used when Starship is unavailable; Starship replaces this function on startup.
function fish_prompt
    set -l last_status $status
    set_color --bold 45d5dc
    printf '%s' $USER
    set_color 748a9f
    printf ' › '
    set_color 70aee5
    printf '%s' (prompt_pwd)
    set_color 748a9f
    fish_git_prompt ' › %s'
    printf '\n'
    if test $last_status -ne 0
        set_color ed7784
    else
        set_color dce7ee
    end
    printf '❯ '
    set_color normal
end
