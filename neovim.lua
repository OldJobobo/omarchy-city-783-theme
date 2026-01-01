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
                bg = "#3d2e1d",                bg_dark = "#3d2e1d",                bg_highlight = "#f67f7f",
                -- Foreground colors
                -- fg: Object properties, builtin types, builtin variables, member access, default text
                fg = "#f0c1c5",                -- fg_dark: Inactive elements, statusline, secondary text
                fg_dark = "#eec1b4",                -- comment: Line highlight, gutter elements, disabled states
                comment = "#e3c0b0",
                -- Accent colors
                -- red: Errors, diagnostics, tags, deletions, breakpoints
                red = "#3d2e1d",                -- orange: Constants, numbers, current line number, git modifications
                orange = "#E73232",                -- yellow: Types, classes, constructors, warnings, numbers, booleans
                yellow = "#c68c71",                -- green: Comments, strings, success states, git additions
                green = "#d7866f",                -- cyan: Parameters, regex, preprocessor, hints, properties
                cyan = "#d97c84",                -- blue: Functions, keywords, directories, links, info diagnostics
                blue = "#CA5B63",                -- purple: Storage keywords, special keywords, identifiers, namespaces
                purple = "#f3e1db",                -- magenta: Function declarations, exception handling, tags
                magenta = "#fdfdfc",            },
        },
        config = function(_, opts)
            require("aether").setup(opts)
            vim.cmd.colorscheme("aether")

            -- Enable hot reload
            require("aether.hotreload").setup()

            vim.api.nvim_create_autocmd("VimEnter", {
                callback = function()
                    if vim.g.colors_name ~= "aether" then
                        vim.cmd.colorscheme("aether")
                    end
                end,
            })
        end,
    },
    {
        "LazyVim/LazyVim",
        opts = {
            colorscheme = "aether",
        },
    },
}
