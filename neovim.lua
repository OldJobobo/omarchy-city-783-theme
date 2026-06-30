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
				base00 = "#181a1f", -- Default background
				base01 = "#20232a", -- Lighter background (status bars)
				base02 = "#2b2f37", -- Selection background
				base03 = "#4b515b", -- Comments, invisibles
				base04 = "#6a707a", -- Dark foreground
				base05 = "#b9bec6", -- Default foreground
				base06 = "#d3d7dd", -- Light foreground
				base07 = "#eceff2", -- Light background

				-- Accent colors (base08-base0F)
				base08 = "#e53939", -- Variables, errors, red
				base09 = "#cc1f1f", -- Integers, constants, orange
				base0A = "#9e1a1a", -- Classes, types, yellow
				base0B = "#dce0e6", -- Strings, green
				base0C = "#8f949c", -- Support, regex, cyan
				base0D = "#ad2222", -- Functions, keywords, blue
				base0E = "#c3c8d0", -- Keywords, storage, magenta
				base0F = "#6a3030", -- Deprecated, brown/yellow
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
