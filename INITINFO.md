# INITINFO.md

## Theme overview (universal structure)

This theme is built around a single 16-color terminal palette, plus a small set of UI
background/foreground roles that reuse those same colors. Most files either define:

- A terminal-style palette (colors 0–15 + background/foreground + cursor), or
- UI role colors that reference the palette (GTK/Adwaita, CSS, JSON themes), or
- Semantic highlight roles (Neovim/Zed) that map to palette accents.

The exact hex values are not important here; the goal is to describe how the files are
structured so a script can apply any Base16 scheme consistently.

## File-by-file format and color usage (structure)

### Terminal palettes (ANSI 0–15 + bg/fg)

- `alacritty.toml`
  - TOML sectioned palette:
    - `[colors.primary]` sets `background` and `foreground`
    - `[colors.normal]` maps color0–color7 (black → white)
    - `[colors.bright]` maps color8–color15 (bright_*)
    - `[colors.cursor]` sets cursor color and cursor text color

- `kitty.conf`
  - Plain key/value:
    - `background`, `foreground`
    - `color0`–`color15`

- `ghostty.conf`
  - `background`, `foreground`
  - `palette = N=#RRGGBB` for N=0..15

- `warp.yaml`
  - `background`, `foreground`, `accent`, `cursor`
  - `terminal_colors.normal` and `terminal_colors.bright`
  - `accent` is a single UI accent; `cursor` is a separate slot.

- `colors.fish`
  - Universal variables for Fish shell:
    - `background`, `foreground`, `cursor`
    - `color0`–`color15`
  - Also sets semantic Fish colors (these use named colors like `green`).

- `fzf.fish`
  - Defines `color00`–`color0F` in Base16 style.
  - Injects `FZF_DEFAULT_OPTS` color arguments using those variables.
  - Important: This file assumes `color00`–`color0F` are direct ANSI-like colors, not
    semantic Base16 UI slots.

- `vencord.theme.css`
  - Base16 Discord theme variables: `--color00`–`--color15`.

### UI/GUI themes using palette roles

- `gtk.css`
  - Defines the palette as `@define-color` values and maps them to GTK/Adwaita roles.
  - Uses alpha() for subtle borders and headerbar backgrounds.

- `aether.override.css`
  - Similar to `gtk.css`, with more granular role variables.
  - Intended to be copied into `~/.config/aether/theme.override.css`.

- `steam.css`
  - Adwaita variables in RGB integer form, e.g. `61, 46, 29` (no `#`).
  - Maps the palette into `--adw-*` variables (accent, success, warning, etc).

- `aether.zed.json`
  - Zed theme schema JSON.
  - UI backgrounds/foregrounds map to base UI roles.
  - Syntax colors map to accents.
  - Terminal colors inside Zed are overridden; verify whether bright colors are meant
    to mirror normal colors or use the bright palette.

- `neovim.lua`
  - Uses the `bjarneo/aether.nvim` plugin with a custom `colors` table.
  - Semantic roles (bg, fg, comment, red, orange, yellow, green, cyan, blue, purple,
    magenta) map to the palette but not in strict Base16 ordering.
  - This is a syntax-highlight mapping rather than direct ANSI palette mapping.

### App-specific styling

- `btop.theme`
  - Uses palette colors for UI roles (main_bg, main_fg, selected, borders).
  - Also defines gradients for meters using accent colors.

- `cava_theme`
  - Gradient colors only (no base background/foreground).

- `mako.ini`
  - Notification colors: `text-color`, `border-color`, `background-color`.

- `hyprland.conf`
  - Uses `rgb(RRGGBB)` format (no `#`) for active border color.

- `hyprlock.conf`
  - Uses `rgba(r, g, b, a)` values.
  - Requires conversion from hex to integer RGB + alpha.

- `chromium.theme`
  - Raw RGB tuple `r,g,b` (no `#`, no alpha).

- `waybar.css`
  - Minimal: background and foreground only.

- `wofi.css`
  - Defines `@bg`, `@fg`, and five accent slots (`gray1`..`gray5`).

- `walker.css`
  - Uses `selected-text` as accent; `base`/`background` as UI base; `border` as a UI
    separator/muted tone.

- `swayosd.css`
  - Background, border, label, image, and progress colors derived from palette.

## Per-file inputs and outputs (for scripting)

Use this as a direct checklist for mapping Base16 slots into each file's expected
keys and formats. "Inputs" are Base16 slots or semantic roles; "Outputs" are file
keys/variables to set.

- `alacritty.toml`
  - Inputs: ANSI 0–15, background, foreground, cursor, cursor_text
  - Outputs:
    - `[colors.primary].background`, `[colors.primary].foreground`
    - `[colors.normal].black`..`[colors.normal].white`
    - `[colors.bright].black`..`[colors.bright].white`
    - `[colors.cursor].cursor`, `[colors.cursor].text`

- `kitty.conf`
  - Inputs: ANSI 0–15, background, foreground
  - Outputs:
    - `background`, `foreground`
    - `color0`..`color15`

- `ghostty.conf`
  - Inputs: ANSI 0–15, background, foreground
  - Outputs:
    - `background`, `foreground`
    - `palette = N=#RRGGBB` for N=0..15

- `warp.yaml`
  - Inputs: ANSI 0–15, background, foreground, accent, cursor
  - Outputs:
    - `background`, `foreground`, `accent`, `cursor`
    - `terminal_colors.normal.*`, `terminal_colors.bright.*`

- `colors.fish`
  - Inputs: ANSI 0–15, background, foreground, cursor
  - Outputs:
    - `set -U background`, `set -U foreground`, `set -U cursor`
    - `set -U color0`..`set -U color15`
  - Note: Additional Fish semantic colors are set using color names, not hex.

- `fzf.fish`
  - Inputs: ANSI 0–15 (mapped into Base16-like slots)
  - Outputs:
    - `set -l color00`..`set -l color0F`
    - `FZF_DEFAULT_OPTS` assembled from `--color=...` entries

- `vencord.theme.css`
  - Inputs: ANSI 0–15 (Base16-like slots)
  - Outputs:
    - `--color00`..`--color15`

- `gtk.css`
  - Inputs: background, foreground, accent, muted, border, success, warning, error
  - Outputs:
    - `@define-color background`, `@define-color foreground`
    - Palette colors (`@define-color red`..`@define-color bright_white`)
    - Adwaita role variables (`accent_*`, `window_*`, `headerbar_*`, etc)

- `aether.override.css`
  - Inputs: same as `gtk.css` plus additional UI role variants
  - Outputs:
    - `@define-color background`, `@define-color foreground`
    - Palette colors (`@define-color red`..`@define-color bright_white`)
    - Extensive Adwaita role variables

- `steam.css`
  - Inputs: background, foreground, accent, success, warning, error, border
  - Outputs:
    - `--adw-*-rgb` variables in `r, g, b` format
  - Note: `-fg-a` entries also appear for alpha.

- `aether.zed.json`
  - Inputs: background, foreground, muted, border, accent set, syntax roles, ANSI 0–15
  - Outputs:
    - `style.*` UI roles
    - `syntax.*` token colors
    - `terminal.*` ANSI colors

- `neovim.lua`
  - Inputs: background, foreground, muted/comment, accent roles
  - Outputs:
    - `colors` table keys: `bg`, `bg_dark`, `bg_highlight`, `fg`, `fg_dark`,
      `comment`, `red`, `orange`, `yellow`, `green`, `cyan`, `blue`, `purple`, `magenta`

- `btop.theme`
  - Inputs: background, foreground, selected, border, accent, gradient colors
  - Outputs:
    - `theme[main_bg]`, `theme[main_fg]`, `theme[selected_bg]`, `theme[selected_fg]`,
      `theme[inactive_fg]`, `theme[div_line]`
    - Box outline colors `theme[cpu_box]`, etc
    - Gradient triplets `*_start`, `*_mid`, `*_end`

- `cava_theme`
  - Inputs: gradient colors
  - Outputs:
    - `gradient_color_1`..`gradient_color_8`

- `mako.ini`
  - Inputs: background, foreground, border
  - Outputs:
    - `background-color`, `text-color`, `border-color`

- `hyprland.conf`
  - Inputs: accent (border)
  - Outputs:
    - `col.active_border` (format `rgb(RRGGBB)`)

- `hyprlock.conf`
  - Inputs: background, accent, foreground, placeholder, check
  - Outputs:
    - `$color`, `$inner_color`, `$outer_color`, `$font_color`, `$placeholder_color`,
      `$check_color` (format `rgba(r, g, b, a)`)

- `chromium.theme`
  - Inputs: background (or primary UI background)
  - Outputs:
    - Raw `r,g,b` tuple

- `waybar.css`
  - Inputs: background, foreground
  - Outputs:
    - `@define-color background`, `@define-color foreground`

- `wofi.css`
  - Inputs: background, foreground, 5 accent slots
  - Outputs:
    - `@define-color bg`, `@define-color fg`, `@define-color gray1`..`gray5`,
      `@define-color fg_bright`

- `walker.css`
  - Inputs: background, foreground, border, accent
  - Outputs:
    - `@define-color selected-text`, `@define-color text`, `@define-color base`,
      `@define-color border`, `@define-color foreground`, `@define-color background`

- `swayosd.css`
  - Inputs: background, border, foreground, accent
  - Outputs:
    - `@define-color background-color`, `@define-color border-color`,
      `@define-color label`, `@define-color image`, `@define-color progress`

## Base16 mapping considerations (universal)

Base16 defines 16 color slots: `base00`–`base07` (UI shades) and `base08`–`base0F`
(accent colors). Terminals, GUIs, and syntax highlighters often interpret these
slots differently:

- Terminals expect 16 ANSI colors (0–15). Many Base16 terminal templates map:
  - 0..7 to UI + standard accents (e.g., base00 → black, base08 → red, base0B → green,
    base0A → yellow, base0D → blue, base0E → magenta, base0C → cyan, base05 → white)
  - 8..15 to brighter or alternate shades (e.g., base03, base08, base0B, base0A,
    base0D, base0E, base0C, base07)
  - Some themes instead map base00..base07 directly to color0..color7, which makes
    the ANSI palette match the UI grays rather than the classic red/green/yellow/etc.

- GUI apps usually use Base16 for UI roles:
  - `base00` = background
  - `base01`/`base02` = surfaces and subtle UI layers
  - `base03` = comments, separators, muted borders
  - `base04`/`base05` = muted/normal foreground
  - `base06`/`base07` = brighter foreground or highlights
  - `base08`–`base0F` = accents (error/success/warning/info/links)

- Syntax highlighting (e.g., Neovim, Zed) often maps `base08`–`base0F` to token roles
  (errors, strings, keywords, functions, etc), while UI uses `base00`–`base07`.
  This repo’s `neovim.lua` uses semantic names rather than Base16 slots, so a script
  must translate from Base16 to those semantic roles.

## Base16 vs ANSI in this theme (behavioral)

- Terminal configs expect ANSI 0–15 directly.
- GUI configs expect semantic UI roles (background/foreground/border/accent) mapped
  from a smaller subset of the palette.
- Editor configs expect semantic syntax roles mapped from accent colors.
- Some files label slots with Base16-like names (`color00`–`color0F`) but still
  expect ANSI-like values.

## Suggested mapping strategy for a Base16 -> theme script

1) Choose a canonical Base16 mapping for ANSI 0–15 and use it consistently.
   A common Base16 terminal mapping is:

   - ANSI 0  = base00
   - ANSI 1  = base08
   - ANSI 2  = base0B
   - ANSI 3  = base0A
   - ANSI 4  = base0D
   - ANSI 5  = base0E
   - ANSI 6  = base0C
   - ANSI 7  = base05
   - ANSI 8  = base03
   - ANSI 9  = base08
   - ANSI 10 = base0B
   - ANSI 11 = base0A
   - ANSI 12 = base0D
   - ANSI 13 = base0E
   - ANSI 14 = base0C
   - ANSI 15 = base07

   This avoids mapping UI grays into the standard ANSI red/green/yellow slots.

2) Map Base16 UI slots to GUI roles:

   - background: base00
   - foreground: base05
   - secondary/muted text: base04
   - borders/lines: base03
   - selected/active surfaces: base01 or base02
   - highlight/hover: base02

3) Map accents to semantic roles:

   - error/destructive: base08
   - warning: base0A
   - success: base0B
   - info/links: base0D or base0C
   - accent: base0D (used as blue in this theme)

4) Handle format conversions:

   - Hex (`#RRGGBB`) for CSS, JSON, TOML, YAML, INI, Fish.
   - `rgb(HEX)` for Hyprland (e.g., `rgb(d97c84)`).
   - `rgba(r, g, b, a)` for Hyprlock (integers + float alpha).
   - `r, g, b` for Chromium/Adwaita overrides (`steam.css`).

5) Special cases to preserve:

   - `aether.zed.json` uses non-bright ANSI colors for terminal bright colors.
     Decide whether to keep this behavior or align with the terminal palette.
   - `fzf.fish` expects Base16 slots but currently mirrors ANSI slots.
     Decide whether to keep ANSI parity or switch to semantic Base16 mapping.
   - `wofi.css` uses `gray1..gray5` names but they are accents; a script should map
     them intentionally, not assume true neutrals.

## Normalization table (Base16 -> ANSI -> semantic roles)

Use this table to keep consistent meaning across terminals, GUI, and editors. If you
prefer a different Base16 terminal mapping, change the ANSI column but keep the
semantic roles stable.

Base16 slots:

- UI shades: base00..base07
- Accents: base08..base0F

Recommended ANSI mapping (common Base16):

- ANSI 0  = base00
- ANSI 1  = base08
- ANSI 2  = base0B
- ANSI 3  = base0A
- ANSI 4  = base0D
- ANSI 5  = base0E
- ANSI 6  = base0C
- ANSI 7  = base05
- ANSI 8  = base03
- ANSI 9  = base08
- ANSI 10 = base0B
- ANSI 11 = base0A
- ANSI 12 = base0D
- ANSI 13 = base0E
- ANSI 14 = base0C
- ANSI 15 = base07

Semantic roles (suggested):

- background: base00
- surface: base01
- surface_alt: base02
- border/muted: base03
- muted_text: base04
- foreground: base05
- bright_text: base06
- highlight_text: base07
- error/destructive: base08
- warning: base0A
- success: base0B
- info/links: base0D
- accent_primary: base0D
- accent_secondary: base0C
- accent_tertiary: base0E
- special: base0F

## Quick reference: where colors are defined

- ANSI palettes: `alacritty.toml`, `kitty.conf`, `ghostty.conf`, `warp.yaml`,
  `colors.fish`, `vencord.theme.css`.
- GUI/Adwaita: `gtk.css`, `aether.override.css`, `steam.css`.
- Editor themes: `neovim.lua`, `aether.zed.json`.
- Notifications/launchers: `mako.ini`, `wofi.css`, `walker.css`, `swayosd.css`.
- WM/lock: `hyprland.conf`, `hyprlock.conf`.
- Misc: `btop.theme`, `cava_theme`, `chromium.theme`, `waybar.css`.
