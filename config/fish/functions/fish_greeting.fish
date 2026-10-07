function fish_greeting
    set_color --bold dce7ee
    printf 'Welcome back, '
    set_color 45d5dc
    printf 'Kedar.\n'
    set_color 748a9f
    date '+%A, %d %B · %H:%M'
    set_color normal
    printf '\n'
end
