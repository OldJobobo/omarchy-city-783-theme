return {
	{
		"bjarneo/aether.nvim",
		branch = "v2",
		name = "aether",
		priority = 1000,
		opts = {
			transparent = false,
			colors = {
				-- Monotone shades (base00-base07)
				base00 = "#1F1F1F", -- Default background
				base01 = "#d12b2b", -- Lighter background (status bars)
				base02 = "#d12b2b", -- Selection background
				base03 = "#4b515b", -- Comments, invisibles
				base04 = "#ad2222", -- Dark foreground
				base05 = "#b9bec6", -- Default foreground
				base06 = "#eceff2", -- Light foreground
				base07 = "#332222", -- Light background

				-- Accent colors (base08-base0F)
				base08 = "#d12b2b", -- Variables, errors, red
				base09 = "#d12b2b", -- Integers, constants, orange
				base0A = "#9e1a1a", -- Classes, types, yellow
				base0B = "#eceff2", -- Strings, green
				base0C = "#b9bec6", -- Support, regex, cyan
				base0D = "#ad2222", -- Functions, keywords, blue
				base0E = "#c3c8d0", -- Keywords, storage, magenta
				base0F = "#8f949c", -- Deprecated, brown/yellow
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
