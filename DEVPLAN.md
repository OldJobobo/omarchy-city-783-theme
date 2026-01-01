# DEVPLAN.md

## Goal

Create a script that reads a Base16 YAML scheme and applies it across all theme files
in this repo, preserving each file’s format and semantic expectations.

## Scope and inputs

- Input: Base16 YAML with `base00`–`base0F` keys (hex `#RRGGBB`).
- Targets: All theme files in the repository (see `INITINFO.md` for mapping structure).
- Output: Updated files with correct palette mappings and format conversions.

## Mapping strategy

1) Normalize Base16 into:
   - ANSI 0–15 (terminal palette)
   - UI roles (background, foreground, muted, border, accent, success, warning, error)
   - Syntax roles (editor token colors)
2) Use a single canonical mapping for ANSI 0–15 (document in code and README).
3) Derive UI roles from Base16 UI shades and accents (see `INITINFO.md`).
4) Convert to file-specific formats (hex, rgb, rgba, etc).

## Script design

### Language and dependencies

- Prefer a small, portable script (Python or Node).
- Use a YAML parser:
  - Python: `pyyaml`
  - Node: `yaml` package

### Architecture

- `parse_base16(input_path)` -> dict of base00..base0F.
- `build_palette(base16)` -> dict:
  - `ansi[0..15]`
  - `ui` roles (background, foreground, border, accent, etc)
  - `syntax` roles (keyword, function, string, etc)
- `render_targets(palette)` -> per-file key/value replacements.
- `apply_changes(files, replacements, dry_run)` -> write updated files or produce a
  patch preview.

## Safety and non-destructive workflow

1) Default to dry-run mode:
   - Print a summary of file changes and a unified diff preview.
2) Write backups before editing:
   - e.g. copy to `.bak` or keep a `backup/` directory.
3) Only overwrite when:
   - `--apply` flag is set
   - `--yes` is provided (or a confirmation prompt is accepted)

## File update approach

- Use deterministic formatting:
  - Preserve existing ordering and spacing.
  - Only replace color values, not keys or comments.
- Implement per-file adapters:
  - `alacritty.toml`: update `[colors.primary]`, `[colors.normal]`, `[colors.bright]`.
  - `kitty.conf`: update `background`, `foreground`, `color0`–`color15`.
  - `ghostty.conf`: update `background`, `foreground`, `palette = N=#RRGGBB`.
  - `warp.yaml`: update `background`, `foreground`, `accent`, `cursor`, and palettes.
  - `gtk.css` / `aether.override.css`: update palette and role variables.
  - `steam.css`: update `--adw-*-rgb` values.
  - `neovim.lua`: update semantic color table.
  - `aether.zed.json`: update UI roles, syntax roles, and terminal ANSI colors.
  - `btop.theme`, `mako.ini`, `wofi.css`, `walker.css`, `swayosd.css`:
    update their role colors.
  - `hyprland.conf`, `hyprlock.conf`, `chromium.theme`:
    update their special formats.

## Validation tools

### Scripted checks (non-destructive)

- `scripts/preview.sh`:
  - Runs the main script in dry-run mode
  - Outputs `diff` per file
- `scripts/validate.sh`:
  - Verifies all required files were updated
  - Checks hex formatting is valid
  - Confirms ANSI 0–15 mapping is complete

### Manual checks

- Apply theme in a terminal to validate ANSI colors.
- Open Neovim/Zed to confirm syntax mapping and UI roles.
- Check GTK/Adwaita apps for background/foreground contrast.

## Suggested CLI interface

- `apply-theme --scheme city-783.yaml --dry-run`
- `apply-theme --scheme city-783.yaml --apply --backup`
- `apply-theme --scheme city-783.yaml --apply --backup --yes`

## Deliverables

- `scripts/apply-theme` (or `apply-theme.py`): main script.
- `scripts/preview.sh`: dry-run wrapper.
- `scripts/validate.sh`: sanity checks.
- Updated documentation in `INITINFO.md` if mappings change.

## Development phases

### Phase 1: Ghostty + Neovim adapters

Goal: Implement the first two file adapters and prove end-to-end mapping correctness.

- Build mapping core:
  - Parse Base16 YAML to `base00`–`base0F`.
  - Normalize to ANSI 0–15 and semantic roles.
- Implement Ghostty adapter:
  - Update `background`, `foreground`, and `palette = N=#RRGGBB` lines.
  - Preserve ordering and spacing.
- Implement Neovim adapter:
  - Update the `colors` table in `neovim.lua` only.
  - Keep keys/ordering intact; only replace hex values.
- Add dry-run support:
  - Print unified diff for `ghostty.conf` and `neovim.lua`.
- Add validation:
  - Confirm all expected keys exist and were replaced.
  - Ensure hex formatting is valid.

### Phase 2: Terminal adapters

Goal: Extend coverage to other terminal configs.

- Add adapters for `alacritty.toml`, `kitty.conf`, `warp.yaml`, `colors.fish`,
  `fzf.fish`, and `vencord.theme.css`.
- Validate ANSI 0–15 mapping consistency across all terminal targets.

### Phase 3: GUI adapters

Goal: Apply Base16 to GTK/Adwaita and UI CSS targets.

- Add adapters for `gtk.css`, `aether.override.css`, `steam.css`, `waybar.css`,
  `wofi.css`, `walker.css`, `swayosd.css`, `mako.ini`, `btop.theme`, `cava_theme`.
- Add format conversions for `rgb(...)` and `r, g, b` tuples.

### Phase 4: Editor + WM targets

Goal: Complete editor themes and window-manager-specific formats.

- Add adapters for `aether.zed.json`, `hyprland.conf`, `hyprlock.conf`,
  `chromium.theme`.
- Review special cases and document any intentional deviations.
