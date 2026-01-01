set -l color00 '#3d2e1d'
set -l color01 '#3d2e1d'
set -l color02 '#d7866f'
set -l color03 '#c68c71'
set -l color04 '#CA5B63'
set -l color05 '#f3e1db'
set -l color06 '#d97c84'
set -l color07 '#f0c1c5'
set -l color08 '#e3c0b0'
set -l color09 '#3d2e1d'
set -l color0A '#d7866f'
set -l color0B '#c68c71'
set -l color0C '#CA5B63'
set -l color0D '#f3e1db'
set -l color0E '#d97c84'
set -l color0F '#ffffff'

set -l FZF_NON_COLOR_OPTS

for arg in (echo $FZF_DEFAULT_OPTS | tr " " "\n")
    if not string match -q -- "--color*" $arg
        set -a FZF_NON_COLOR_OPTS $arg
    end
end

set -Ux FZF_DEFAULT_OPTS "$FZF_NON_COLOR_OPTS"" --color=bg+:$color00,bg:$color00,spinner:$color0E,hl:$color0D"" --color=fg:$color07,header:$color0D,info:$color0A,pointer:$color0E"" --color=marker:$color0E,fg+:$color06,prompt:$color0A,hl+:$color0D"
