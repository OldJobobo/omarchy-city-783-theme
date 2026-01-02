return {
    {
        "bjarneo/aether.nvim",
        branch = "v2",
        name = "aether",
        priority = 1000,
        opts = {
            transparent = false,
            colors = {
                -- Background colors
                bg = "#181a1f",
                bg_dark = "#181a1f",
                bg_highlight = "#2b2f37",

                -- Foreground colors
                -- fg: Object properties, builtin types, builtin variables, member access, default text
                fg = "#b9bec6",
                -- fg_dark: Inactive elements, statusline, secondary text
                fg_dark = "#6a707a",
                -- comment: Line highlight, gutter elements, disabled states
                comment = "#4b515b",

                -- Accent colors
                -- red: Errors, diagnostics, tags, deletions, breakpoints
                red = "#b31414",
                -- orange: Constants, numbers, current line number, git modifications
                orange = "#cc1f1f",
                -- yellow: Types, classes, constructors, warnings, numbers, booleans
                yellow = "#9e1a1a",
                -- green: Comments, strings, success states, git additions
                green = "#d12b2b",
                -- cyan: Parameters, regex, preprocessor, hints, properties
                cyan = "#8f949c",
                -- blue: Functions, keywords, directories, links, info diagnostics
                blue = "#ad2222",
                -- purple: Storage keywords, special keywords, identifiers, namespaces
                purple = "#c3c8d0",
                -- magenta: Function declarations, exception handling, tags
                magenta = "#e9edf0",
            },
        },
        config = function(_, opts)
            require("aether").setup(opts)
            vim.cmd.colorscheme("aether")

            -- Enable hot reload
            require("aether.hotreload").setup()
        end,
    },
    {
        "LazyVim/LazyVim",
        opts = {
            colorscheme = "aether",
        },
    },
}
