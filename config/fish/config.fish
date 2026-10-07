if status is-interactive
    set -g fish_color_normal dce7ee
    set -g fish_color_command 45d5dc
    set -g fish_color_param dce7ee
    set -g fish_color_error ed7784
    set -g fish_color_autosuggestion 748a9f
    set -g fish_color_quote 72c9a7
    set -g fish_pager_color_prefix 45d5dc
    set -g fish_pager_color_selected_background --background=122735
    if type -q starship
        starship init fish | source
    end
    if type -q zoxide
        zoxide init fish | source
    end
end
