set -l color00 '#181a1f'
set -l color01 '#b31414'
set -l color02 '#d12b2b'
set -l color03 '#9e1a1a'
set -l color04 '#ad2222'
set -l color05 '#c3c8d0'
set -l color06 '#8f949c'
set -l color07 '#b9bec6'
set -l color08 '#4b515b'
set -l color09 '#b31414'
set -l color0A '#d12b2b'
set -l color0B '#9e1a1a'
set -l color0C '#ad2222'
set -l color0D '#c3c8d0'
set -l color0E '#8f949c'
set -l color0F '#eceff2'

set -l FZF_NON_COLOR_OPTS

for arg in (echo $FZF_DEFAULT_OPTS | tr " " "\n")
    if not string match -q -- "--color*" $arg
        set -a FZF_NON_COLOR_OPTS $arg
    end
end

set -Ux FZF_DEFAULT_OPTS "$FZF_NON_COLOR_OPTS"" --color=bg+:$color00,bg:$color00,spinner:$color0E,hl:$color0D"" --color=fg:$color07,header:$color0D,info:$color0A,pointer:$color0E"" --color=marker:$color0E,fg+:$color06,prompt:$color0A,hl+:$color0D"
