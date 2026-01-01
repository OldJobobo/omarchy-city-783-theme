# Repository Guidelines

## Project Structure & Module Organization

This repository is a standalone Omarchy theme. There is no application code; each file
is a configuration or style target for a specific app.

- Root configs: terminal themes (`alacritty.toml`, `kitty.conf`, `ghostty.conf`,
  `warp.yaml`), editor themes (`neovim.lua`, `aether.zed.json`), notifications and UI
  (`mako.ini`, `waybar.css`, `wofi.css`, `walker.css`, `swayosd.css`), and window
  manager/lock (`hyprland.conf`, `hyprlock.conf`).
- GTK/Adwaita styling: `gtk.css`, `aether.override.css`, `steam.css`.
- Assets: `backgrounds/`.
- Reference analysis: `INITINFO.md` documents mapping structure for Base16.

## Build, Test, and Development Commands

This theme repo has no build or test tooling. Updates are applied by editing the
configuration files directly. Use targeted edits rather than global search/replace
when updating color roles.

## Coding Style & Naming Conventions

- Preserve the existing file format and key order for each target app.
- Keep values in the format expected by the target:
  - `#RRGGBB` hex for CSS/JSON/TOML/YAML/INI/Fish.
  - `rgb(RRGGBB)` for Hyprland.
  - `rgba(r, g, b, a)` for Hyprlock.
  - `r, g, b` tuples for Chromium/Adwaita overrides.
- Use ASCII only unless the file already contains Unicode.

## Testing Guidelines

There are no automated tests. Validate changes by applying the theme in the target
apps and checking:

- Terminal ANSI 0–15 mapping.
- UI background/foreground contrast.
- Syntax highlighting colors in editors.

## Commit & Pull Request Guidelines

Git history is not available in this directory, so no commit conventions can be
derived. If you add commits, use concise, imperative messages (e.g., "Update GTK role
mapping"). For PRs, include a brief summary of affected apps and, if applicable,
screenshots of UI changes.

## Configuration Tips

When scripting theme updates, follow the Base16 mapping guidance in `INITINFO.md` and
update all target formats in a single pass to keep palette consistency across apps.
