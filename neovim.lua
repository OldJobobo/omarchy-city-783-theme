return {
	{
		"bjarneo/aether.nvim",
		branch = "v3",
		name = "aether",
		priority = 1000,
		opts = {
			transparent = false,
			colors = {
				accent = "#ad2222",
				cursor = "#eceff2",
				foreground = "#b9bec6",
				background = "#181a1f",
				selection_foreground = "#eceff2",
				selection_background = "#2b2f37",

				bg = "#181a1f",
				lighter_bg = "#20232a",
				selection = "#2b2f37",
				muted = "#8f949c",
				dark_fg = "#8f949c",
				fg = "#b9bec6",
				light_fg = "#d3d7dd",
				bright_fg = "#eceff2",

				red = "#ff5c5c",
				orange = "#f04a4a",
				yellow = "#f04a4a",
				green = "#dce0e6",
				cyan = "#8f949c",
				blue = "#ff5c5c",
				purple = "#c3c8d0",
				magenta = "#c3c8d0",
				brown = "#6a3030",

				dark_bg = "#101216",
				darker_bg = "#090a0d",
				bright_red = "#ff5c5c",
				bright_yellow = "#f04a4a",
				bright_green = "#eceff2",
				bright_cyan = "#aab0b9",
				bright_blue = "#dce0e6",
				bright_purple = "#f5f7f9",
				bright_magenta = "#f5f7f9",
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
