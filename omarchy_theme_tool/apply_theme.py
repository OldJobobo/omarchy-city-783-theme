#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys

BASE16_KEYS = [f"base{n:02X}" for n in range(16)]

ANSI_MAP = {
    0: "base00",
    1: "base08",
    2: "base0B",
    3: "base0A",
    4: "base0D",
    5: "base0E",
    6: "base0C",
    7: "base05",
    8: "base03",
    9: "base08",
    10: "base0B",
    11: "base0A",
    12: "base0D",
    13: "base0E",
    14: "base0C",
    15: "base07",
}

NEOVIM_KEYS = {
    "bg": "base00",
    "bg_dark": "base00",
    "bg_highlight": "base02",
    "fg": "base05",
    "fg_dark": "base04",
    "comment": "base03",
    "red": "base08",
    "orange": "base09",
    "yellow": "base0A",
    "green": "base0B",
    "cyan": "base0C",
    "blue": "base0D",
    "purple": "base0E",
    "magenta": "base0F",
}

ANSI_RESET = "\x1b[0m"


def hex_to_rgb(hex_color):
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return None
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def swatch(hex_color, label):
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return label
    r, g, b = rgb
    return f"\x1b[48;2;{r};{g};{b}m {label} {ANSI_RESET}"


def format_report_line(entry):
    match = re.search(r"(#[0-9A-Fa-f]{6})", entry)
    if not match:
        return entry
    hex_color = match.group(1)
    return f"{swatch(hex_color, hex_color)} {entry}"

def load_base16(path):
    base16 = {}
    line_re = re.compile(r"^\s*(base[0-9A-Fa-f]{2})\s*:\s*['\"]?(#[0-9A-Fa-f]{6})")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            match = line_re.match(line)
            if not match:
                continue
            raw_hex = match.group(1)[4:]
            key = f"base{int(raw_hex, 16):02X}"
            value = match.group(2)
            base16[key] = value

    missing = [k for k in BASE16_KEYS if k not in base16]
    if missing:
        raise ValueError(f"Missing Base16 keys: {', '.join(missing)}")

    return base16


def build_palette(base16):
    ansi = {i: base16[ANSI_MAP[i]] for i in range(16)}
    ui = {
        "background": base16["base00"],
        "foreground": base16["base05"],
        "accent": base16["base0D"],
        "cursor": base16["base05"],
    }
    neovim = {key: base16[val] for key, val in NEOVIM_KEYS.items()}
    return {"ansi": ansi, "ui": ui, "neovim": neovim, "base16": base16}


def update_ghostty(contents, palette):
    ansi = palette["ansi"]
    ui = palette["ui"]
    replaced = {"background": False, "foreground": False, "palette": set()}
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        if re.match(r"^\s*background\s*=", line):
            new_line, count = re.subn(
                r"^(\s*background\s*=\s*)#?[0-9A-Fa-f]{6}",
                lambda m: f"{m.group(1)}{ui['background']}",
                line,
            )
            if count:
                replaced["background"] = True
                report.append(f"background -> {ui['background']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*foreground\s*=", line):
            new_line, count = re.subn(
                r"^(\s*foreground\s*=\s*)#?[0-9A-Fa-f]{6}",
                lambda m: f"{m.group(1)}{ui['foreground']}",
                line,
            )
            if count:
                replaced["foreground"] = True
                report.append(f"foreground -> {ui['foreground']}")
            new_lines.append(new_line)
            continue

        pal_match = re.match(r"^(\s*palette\s*=\s*)(\d+)=#?[0-9A-Fa-f]{6}", line)
        if pal_match:
            index = int(pal_match.group(2))
            if index in ansi:
                new_line = re.sub(
                    r"^(\s*palette\s*=\s*)\d+=#?[0-9A-Fa-f]{6}",
                    lambda m: f"{m.group(1)}{index}={ansi[index]}",
                    line,
                )
                replaced["palette"].add(index)
                report.append(f"palette[{index}] -> {ansi[index]}")
                new_lines.append(new_line)
                continue

        new_lines.append(line)

    missing = []
    if not replaced["background"]:
        missing.append("background")
    if not replaced["foreground"]:
        missing.append("foreground")
    missing_palette = [i for i in range(16) if i not in replaced["palette"]]
    if missing:
        report.append("missing keys: " + ", ".join(missing))
    if missing_palette:
        report.append("missing palette indexes: " + ", ".join(str(i) for i in missing_palette))

    return "".join(new_lines), report


def update_neovim(contents, palette):
    neovim = palette["neovim"]
    updated = contents
    report = []
    replaced_keys = set()

    for key, value in neovim.items():
        pattern = rf"(\b{re.escape(key)}\s*=\s*)(['\"]?)(#[0-9A-Fa-f]{{6}})(['\"]?)"
        updated, count = re.subn(
            pattern,
            lambda m, v=value: f"{m.group(1)}{m.group(2)}{v}{m.group(4)}",
            updated,
        )
        if count:
            replaced_keys.add(key)
            report.append(f"{key} -> {value}")

    missing = [key for key in neovim.keys() if key not in replaced_keys]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return updated, report


def update_alacritty(contents, palette):
    ansi = palette["ansi"]
    ui = palette["ui"]
    section = None
    replaced = {
        "primary": {"background": False, "foreground": False},
        "cursor": {"text": False, "cursor": False},
        "normal": set(),
        "bright": set(),
    }
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        header_match = re.match(r"^\s*\[(.+)\]\s*$", line)
        if header_match:
            section = header_match.group(1).strip()
            new_lines.append(line)
            continue

        if section == "colors.primary":
            if re.match(r"^\s*background\s*=", line):
                new_line, count = re.subn(
                    r"^(\s*background\s*=\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                    lambda m: f"{m.group(1)}{m.group(2)}{ui['background']}{m.group(2)}",
                    line,
                )
                if count:
                    replaced["primary"]["background"] = True
                    report.append(f"colors.primary.background -> {ui['background']}")
                new_lines.append(new_line)
                continue
            if re.match(r"^\s*foreground\s*=", line):
                new_line, count = re.subn(
                    r"^(\s*foreground\s*=\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                    lambda m: f"{m.group(1)}{m.group(2)}{ui['foreground']}{m.group(2)}",
                    line,
                )
                if count:
                    replaced["primary"]["foreground"] = True
                    report.append(f"colors.primary.foreground -> {ui['foreground']}")
                new_lines.append(new_line)
                continue

        if section == "colors.cursor":
            if re.match(r"^\s*text\s*=", line):
                new_line, count = re.subn(
                    r"^(\s*text\s*=\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                    lambda m: f"{m.group(1)}{m.group(2)}{ui['background']}{m.group(2)}",
                    line,
                )
                if count:
                    replaced["cursor"]["text"] = True
                    report.append(f"colors.cursor.text -> {ui['background']}")
                new_lines.append(new_line)
                continue
            if re.match(r"^\s*cursor\s*=", line):
                new_line, count = re.subn(
                    r"^(\s*cursor\s*=\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                    lambda m: f"{m.group(1)}{m.group(2)}{ui['cursor']}{m.group(2)}",
                    line,
                )
                if count:
                    replaced["cursor"]["cursor"] = True
                    report.append(f"colors.cursor.cursor -> {ui['cursor']}")
                new_lines.append(new_line)
                continue

        if section == "colors.normal" or section == "colors.bright":
            target = "normal" if section == "colors.normal" else "bright"
            color_map = {
                "black": 0,
                "red": 1,
                "green": 2,
                "yellow": 3,
                "blue": 4,
                "magenta": 5,
                "cyan": 6,
                "white": 7,
            }
            for name, base_index in color_map.items():
                if re.match(rf"^\s*{name}\s*=", line):
                    index = base_index if target == "normal" else base_index + 8
                    new_line, count = re.subn(
                        rf"^(\s*{name}\s*=\s*)(['\"]?)#?[0-9A-Fa-f]{{6}}\2",
                        lambda m: f"{m.group(1)}{m.group(2)}{ansi[index]}{m.group(2)}",
                        line,
                    )
                    if count:
                        replaced[target].add(name)
                        report.append(f"colors.{target}.{name} -> {ansi[index]}")
                    new_lines.append(new_line)
                    break
            else:
                new_lines.append(line)
            continue

        new_lines.append(line)

    missing = []
    if not replaced["primary"]["background"] or not replaced["primary"]["foreground"]:
        missing.append("colors.primary")
    if not replaced["cursor"]["text"] or not replaced["cursor"]["cursor"]:
        missing.append("colors.cursor")
    for section_name in ("normal", "bright"):
        if len(replaced[section_name]) != 8:
            missing.append(f"colors.{section_name}")
    if missing:
        report.append("missing sections/keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_kitty(contents, palette):
    ansi = palette["ansi"]
    ui = palette["ui"]
    replaced = {"background": False, "foreground": False, "colors": set()}
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        if re.match(r"^\s*background\s+", line):
            new_line, count = re.subn(
                r"^(\s*background\s+)#?[0-9A-Fa-f]{6}(.*)$",
                lambda m: f"{m.group(1)}{ui['background']}{m.group(2)}",
                line,
            )
            if count:
                replaced["background"] = True
                report.append(f"background -> {ui['background']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*foreground\s+", line):
            new_line, count = re.subn(
                r"^(\s*foreground\s+)#?[0-9A-Fa-f]{6}(.*)$",
                lambda m: f"{m.group(1)}{ui['foreground']}{m.group(2)}",
                line,
            )
            if count:
                replaced["foreground"] = True
                report.append(f"foreground -> {ui['foreground']}")
            new_lines.append(new_line)
            continue

        color_match = re.match(r"^\s*color(\d{1,2})\s+#?[0-9A-Fa-f]{6}", line)
        if color_match:
            index = int(color_match.group(1))
            if index in ansi:
                new_line = re.sub(
                    r"^(\s*color\d{1,2}\s+)#?[0-9A-Fa-f]{6}(.*)$",
                    lambda m: f"{m.group(1)}{ansi[index]}{m.group(2)}",
                    line,
                )
                replaced["colors"].add(index)
                report.append(f"color{index} -> {ansi[index]}")
                new_lines.append(new_line)
                continue

        new_lines.append(line)

    missing = []
    if not replaced["background"] or not replaced["foreground"]:
        missing.append("background/foreground")
    missing_colors = [i for i in range(16) if i not in replaced["colors"]]
    if missing_colors:
        missing.append("colors: " + ", ".join(str(i) for i in missing_colors))
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_warp(contents, palette):
    ansi = palette["ansi"]
    ui = palette["ui"]
    section = None
    in_terminal_colors = False
    replaced = {
        "background": False,
        "foreground": False,
        "accent": False,
        "cursor": False,
        "normal": set(),
        "bright": set(),
    }
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        if re.match(r"^\s*terminal_colors:\s*$", line):
            in_terminal_colors = True
            section = None
            new_lines.append(line)
            continue
        if in_terminal_colors and re.match(r"^\s*normal:\s*$", line):
            section = "normal"
            new_lines.append(line)
            continue
        if in_terminal_colors and re.match(r"^\s*bright:\s*$", line):
            section = "bright"
            new_lines.append(line)
            continue
        if re.match(r"^[A-Za-z_].*:\s*$", line):
            in_terminal_colors = False
            section = None

        if re.match(r"^\s*background:\s*", line):
            new_line, count = re.subn(
                r"^(\s*background:\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                lambda m: f"{m.group(1)}{m.group(2)}{ui['background']}{m.group(2)}",
                line,
            )
            if count:
                replaced["background"] = True
                report.append(f"background -> {ui['background']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*foreground:\s*", line):
            new_line, count = re.subn(
                r"^(\s*foreground:\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                lambda m: f"{m.group(1)}{m.group(2)}{ui['foreground']}{m.group(2)}",
                line,
            )
            if count:
                replaced["foreground"] = True
                report.append(f"foreground -> {ui['foreground']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*accent:\s*", line):
            new_line, count = re.subn(
                r"^(\s*accent:\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                lambda m: f"{m.group(1)}{m.group(2)}{ui['accent']}{m.group(2)}",
                line,
            )
            if count:
                replaced["accent"] = True
                report.append(f"accent -> {ui['accent']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*cursor:\s*", line):
            new_line, count = re.subn(
                r"^(\s*cursor:\s*)(['\"]?)#?[0-9A-Fa-f]{6}\2",
                lambda m: f"{m.group(1)}{m.group(2)}{ui['cursor']}{m.group(2)}",
                line,
            )
            if count:
                replaced["cursor"] = True
                report.append(f"cursor -> {ui['cursor']}")
            new_lines.append(new_line)
            continue

        if section in ("normal", "bright"):
            color_map = {
                "black": 0,
                "red": 1,
                "green": 2,
                "yellow": 3,
                "blue": 4,
                "magenta": 5,
                "cyan": 6,
                "white": 7,
            }
            for name, base_index in color_map.items():
                if re.match(rf"^\s*{name}:\s*", line):
                    index = base_index if section == "normal" else base_index + 8
                    new_line, count = re.subn(
                        rf"^(\s*{name}:\s*)(['\"]?)#?[0-9A-Fa-f]{{6}}\2",
                        lambda m: f"{m.group(1)}{m.group(2)}{ansi[index]}{m.group(2)}",
                        line,
                    )
                    if count:
                        replaced[section].add(name)
                        report.append(f"terminal_colors.{section}.{name} -> {ansi[index]}")
                    new_lines.append(new_line)
                    break
            else:
                new_lines.append(line)
            continue

        new_lines.append(line)

    missing = []
    for key in ("background", "foreground", "accent", "cursor"):
        if not replaced[key]:
            missing.append(key)
    for section_name in ("normal", "bright"):
        if len(replaced[section_name]) != 8:
            missing.append(section_name)
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_colors_fish(contents, palette):
    ansi = palette["ansi"]
    ui = palette["ui"]
    replaced = {"background": False, "foreground": False, "cursor": False, "colors": set()}
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        if re.match(r"^\s*set -U background\s+", line):
            new_line, count = re.subn(
                r"^(\s*set -U background\s+)'?#[0-9A-Fa-f]{6}'?",
                lambda m: f"{m.group(1)}'{ui['background']}'",
                line,
            )
            if count:
                replaced["background"] = True
                report.append(f"background -> {ui['background']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*set -U foreground\s+", line):
            new_line, count = re.subn(
                r"^(\s*set -U foreground\s+)'?#[0-9A-Fa-f]{6}'?",
                lambda m: f"{m.group(1)}'{ui['foreground']}'",
                line,
            )
            if count:
                replaced["foreground"] = True
                report.append(f"foreground -> {ui['foreground']}")
            new_lines.append(new_line)
            continue
        if re.match(r"^\s*set -U cursor\s+", line):
            new_line, count = re.subn(
                r"^(\s*set -U cursor\s+)'?#[0-9A-Fa-f]{6}'?",
                lambda m: f"{m.group(1)}'{ui['cursor']}'",
                line,
            )
            if count:
                replaced["cursor"] = True
                report.append(f"cursor -> {ui['cursor']}")
            new_lines.append(new_line)
            continue

        color_match = re.match(r"^\s*set -U color(\d{1,2})\s+'?#?[0-9A-Fa-f]{6}'?", line)
        if color_match:
            index = int(color_match.group(1))
            if index in ansi:
                new_line = re.sub(
                    r"^(\s*set -U color\d{1,2}\s+)'?#?[0-9A-Fa-f]{6}'?",
                    lambda m: f"{m.group(1)}'{ansi[index]}'",
                    line,
                )
                replaced["colors"].add(index)
                report.append(f"color{index} -> {ansi[index]}")
                new_lines.append(new_line)
                continue

        new_lines.append(line)

    missing = []
    if not replaced["background"] or not replaced["foreground"] or not replaced["cursor"]:
        missing.append("background/foreground/cursor")
    missing_colors = [i for i in range(16) if i not in replaced["colors"]]
    if missing_colors:
        missing.append("colors: " + ", ".join(str(i) for i in missing_colors))
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_fzf_fish(contents, palette):
    ansi = palette["ansi"]
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        match = re.match(r"^(\s*set -l color)([0-9A-Fa-f]{2})\s+'?#?[0-9A-Fa-f]{6}'?", line)
        if match:
            index = int(match.group(2), 16)
            if index in ansi:
                new_line = re.sub(
                    r"^(\s*set -l color[0-9A-Fa-f]{2}\s+)'?#?[0-9A-Fa-f]{6}'?",
                    lambda m: f"{m.group(1)}'{ansi[index]}'",
                    line,
                )
                replaced.add(index)
                report.append(f"color{match.group(2).upper()} -> {ansi[index]}")
                new_lines.append(new_line)
                continue

        new_lines.append(line)

    missing = [i for i in range(16) if i not in replaced]
    if missing:
        report.append("missing color slots: " + ", ".join(f"{i:02X}" for i in missing))

    return "".join(new_lines), report


def update_vencord(contents, palette):
    ansi = palette["ansi"]
    replaced = set()
    report = []

    def repl(match):
        index = int(match.group(1), 10)
        if index in ansi:
            replaced.add(index)
            return f"{match.group(0).split(':')[0]}: {ansi[index]};"
        return match.group(0)

    updated = re.sub(r"--color(\d{2})\s*:\s*#?[0-9A-Fa-f]{6};", repl, contents)
    for index in sorted(replaced):
        report.append(f"--color{index:02d} -> {ansi[index]}")
    missing = [i for i in range(16) if i not in replaced]
    if missing:
        report.append("missing colors: " + ", ".join(str(i) for i in missing))

    return updated, report


def update_hyprland(contents, palette):
    base16 = palette["base16"]
    accent = base16["base0D"].lstrip("#")
    replaced = False
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        if re.match(r"^\s*\$activeBorderColor\s*=", line):
            new_line, count = re.subn(
                r"^(\s*\$activeBorderColor\s*=\s*)rgb\([0-9A-Fa-f]{6}\)",
                lambda m: f"{m.group(1)}rgb({accent})",
                line,
            )
            if count:
                replaced = True
                report.append(f"$activeBorderColor -> #{accent}")
            new_lines.append(new_line)
            continue
        new_lines.append(line)

    if not replaced:
        report.append("missing $activeBorderColor")

    return "".join(new_lines), report


def update_hyprlock(contents, palette):
    base16 = palette["base16"]
    targets = {
        "$color": base16["base00"],
        "$inner_color": base16["base00"],
        "$outer_color": base16["base0D"],
        "$font_color": base16["base07"],
        "$placeholder_color": base16["base07"],
        "$check_color": base16["base0E"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        line_replaced = False
        for name, hex_color in targets.items():
            if re.match(rf"^\s*{re.escape(name)}\s*=", line):
                rgb = hex_to_rgb(hex_color)
                if not rgb:
                    new_lines.append(line)
                    line_replaced = True
                    break
                r, g, b = rgb
                new_line, count = re.subn(
                    rf"^(\s*{re.escape(name)}\s*=\s*rgba\()\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*([0-9.]+)\s*\)",
                    lambda m: f"{m.group(1)}{r}, {g}, {b}, {m.group(2)})",
                    line,
                )
                if count == 0:
                    new_line, count = re.subn(
                        rf"^(\s*{re.escape(name)}\s*=\s*rgba\()\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)",
                        lambda m: f"{m.group(1)}{r}, {g}, {b}, 1)",
                        line,
                    )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {hex_color}")
                new_lines.append(new_line)
                line_replaced = True
                break
        if line_replaced:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_mako(contents, palette):
    base16 = palette["base16"]
    targets = {
        "text-color": base16["base07"],
        "border-color": base16["base0D"],
        "background-color": base16["base00"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for key, value in targets.items():
            if re.match(rf"^\s*{re.escape(key)}\s*=", line):
                new_line, count = re.subn(
                    rf"^(\s*{re.escape(key)}\s*=\s*)#?[0-9A-Fa-f]{{6}}",
                    lambda m: f"{m.group(1)}{value}",
                    line,
                )
                if count:
                    replaced.add(key)
                    report.append(f"{key} -> {value}")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [key for key in targets.keys() if key not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_waybar(contents, palette):
    base16 = palette["base16"]
    targets = {
        "background": base16["base00"],
        "foreground": base16["base05"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for name, value in targets.items():
            if re.match(rf"^\s*@define-color\s+{re.escape(name)}\s+", line):
                new_line, count = re.subn(
                    rf"^(\s*@define-color\s+{re.escape(name)}\s+)#?[0-9A-Fa-f]{{6}}(\s*;)",
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {value}")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_wofi(contents, palette):
    base16 = palette["base16"]
    targets = {
        "bg": base16["base00"],
        "fg": base16["base05"],
        "gray1": base16["base01"],
        "gray2": base16["base02"],
        "gray3": base16["base03"],
        "gray4": base16["base04"],
        "gray5": base16["base05"],
        "fg_bright": base16["base07"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for name, value in targets.items():
            if re.match(rf"^\s*@define-color\s+{re.escape(name)}\s+", line):
                new_line, count = re.subn(
                    rf"^(\s*@define-color\s+{re.escape(name)}\s+)#?[0-9A-Fa-f]{{6}}(\s*;)",
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {value}")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_walker(contents, palette):
    base16 = palette["base16"]
    targets = {
        "selected-text": base16["base0D"],
        "text": base16["base05"],
        "base": base16["base00"],
        "border": base16["base02"],
        "foreground": base16["base05"],
        "background": base16["base00"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for name, value in targets.items():
            if re.match(rf"^\s*@define-color\s+{re.escape(name)}\s+", line):
                new_line, count = re.subn(
                    rf"^(\s*@define-color\s+{re.escape(name)}\s+)#?[0-9A-Fa-f]{{6}}(\s*;)",
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {value}")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_swayosd(contents, palette):
    base16 = palette["base16"]
    targets = {
        "background-color": base16["base00"],
        "border-color": base16["base02"],
        "label": base16["base05"],
        "image": base16["base05"],
        "progress": base16["base0B"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for name, value in targets.items():
            if re.match(rf"^\s*@define-color\s+{re.escape(name)}\s+", line):
                new_line, count = re.subn(
                    rf"^(\s*@define-color\s+{re.escape(name)}\s+)#?[0-9A-Fa-f]{{6}}(\s*;)",
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {value}")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_btop(contents, palette):
    base16 = palette["base16"]
    targets = {
        "main_bg": base16["base00"],
        "main_fg": base16["base05"],
        "title": base16["base0D"],
        "hi_fg": base16["base0E"],
        "selected_bg": base16["base01"],
        "selected_fg": base16["base05"],
        "inactive_fg": base16["base02"],
        "proc_misc": base16["base0D"],
        "cpu_box": base16["base0A"],
        "mem_box": base16["base0A"],
        "net_box": base16["base0A"],
        "proc_box": base16["base0A"],
        "div_line": base16["base02"],
        "temp_start": base16["base0E"],
        "temp_mid": base16["base0D"],
        "temp_end": base16["base0A"],
        "cpu_start": base16["base0E"],
        "cpu_mid": base16["base0D"],
        "cpu_end": base16["base0A"],
        "free_start": base16["base0D"],
        "free_mid": base16["base0B"],
        "free_end": base16["base0B"],
        "cached_start": base16["base0B"],
        "cached_mid": base16["base0B"],
        "cached_end": base16["base0B"],
        "available_start": base16["base0E"],
        "available_mid": base16["base0E"],
        "available_end": base16["base0E"],
        "used_start": base16["base0A"],
        "used_mid": base16["base0A"],
        "used_end": base16["base0A"],
        "download_start": base16["base0B"],
        "download_mid": base16["base0E"],
        "download_end": base16["base0D"],
        "upload_start": base16["base0B"],
        "upload_mid": base16["base0E"],
        "upload_end": base16["base0D"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        match = re.match(r'^\s*theme\[([^\]]+)\]\s*=\s*"#?[0-9A-Fa-f]{6}"', line)
        if match:
            key = match.group(1)
            if key in targets:
                value = targets[key]
                new_line, count = re.subn(
                    r'^(\s*theme\[[^\]]+\]\s*=\s*")#?[0-9A-Fa-f]{6}(")',
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(key)
                    report.append(f"{key} -> {value}")
                    new_lines.append(new_line)
                    continue
        new_lines.append(line)

    missing = [key for key in targets.keys() if key not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_cava(contents, palette):
    base16 = palette["base16"]
    gradient = [
        base16["base0D"],
        base16["base0C"],
        base16["base0B"],
        base16["base0A"],
        base16["base09"],
        base16["base08"],
        base16["base0E"],
        base16["base0F"],
    ]
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        match = re.match(r"^\s*gradient_color_(\d+)\s*=\s*'#[0-9A-Fa-f]{6}'", line)
        if match:
            idx = int(match.group(1))
            if 1 <= idx <= len(gradient):
                value = gradient[idx - 1]
                new_line, count = re.subn(
                    r"^(\s*gradient_color_\d+\s*=\s*')#?[0-9A-Fa-f]{6}(')",
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(idx)
                    report.append(f"gradient_color_{idx} -> {value}")
                    new_lines.append(new_line)
                    continue
        new_lines.append(line)

    missing = [i for i in range(1, 9) if i not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(str(i) for i in missing))

    return "".join(new_lines), report


def update_chromium(contents, palette):
    base16 = palette["base16"]
    rgb = hex_to_rgb(base16["base00"])
    if not rgb:
        return contents, ["missing base00"]
    r, g, b = rgb
    value = f"{r},{g},{b}"
    report = [f"chromium.theme -> {value}"]
    return value + "\n", report


def update_gtk_css(contents, palette):
    ansi = palette["ansi"]
    base16 = palette["base16"]
    targets = {
        "background": base16["base00"],
        "foreground": base16["base05"],
        "black": ansi[0],
        "red": ansi[1],
        "green": ansi[2],
        "yellow": ansi[3],
        "blue": ansi[4],
        "magenta": ansi[5],
        "cyan": ansi[6],
        "white": ansi[7],
        "bright_black": ansi[8],
        "bright_red": ansi[9],
        "bright_green": ansi[10],
        "bright_yellow": ansi[11],
        "bright_blue": ansi[12],
        "bright_magenta": ansi[13],
        "bright_cyan": ansi[14],
        "bright_white": ansi[15],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for name, value in targets.items():
            if re.match(rf"^\s*@define-color\s+{re.escape(name)}\s+", line):
                new_line, count = re.subn(
                    rf"^(\s*@define-color\s+{re.escape(name)}\s+)#?[0-9A-Fa-f]{{6}}(\s*;)",
                    lambda m: f"{m.group(1)}{value}{m.group(2)}",
                    line,
                )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {value}")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_aether_override(contents, palette):
    return update_gtk_css(contents, palette)


def update_steam(contents, palette):
    base16 = palette["base16"]
    targets = {
        "--adw-accent-bg-rgb": base16["base0D"],
        "--adw-accent-fg-rgb": base16["base00"],
        "--adw-accent-rgb": base16["base0D"],
        "--adw-destructive-bg-rgb": base16["base08"],
        "--adw-destructive-fg-rgb": base16["base07"],
        "--adw-destructive-rgb": base16["base08"],
        "--adw-success-bg-rgb": base16["base0B"],
        "--adw-success-fg-rgb": base16["base00"],
        "--adw-success-rgb": base16["base0B"],
        "--adw-warning-bg-rgb": base16["base0A"],
        "--adw-warning-fg-rgb": base16["base00"],
        "--adw-warning-rgb": base16["base0A"],
        "--adw-error-bg-rgb": base16["base08"],
        "--adw-error-fg-rgb": base16["base00"],
        "--adw-error-rgb": base16["base08"],
        "--adw-window-bg-rgb": base16["base00"],
        "--adw-window-fg-rgb": base16["base05"],
        "--adw-view-bg-rgb": base16["base00"],
        "--adw-view-fg-rgb": base16["base05"],
        "--adw-headerbar-bg-rgb": base16["base00"],
        "--adw-headerbar-fg-rgb": base16["base05"],
        "--adw-headerbar-border-rgb": base16["base02"],
        "--adw-headerbar-backdrop-rgb": base16["base00"],
        "--adw-sidebar-bg-rgb": base16["base00"],
        "--adw-sidebar-fg-rgb": base16["base05"],
        "--adw-sidebar-backdrop-rgb": base16["base01"],
        "--adw-secondary-sidebar-bg-rgb": base16["base00"],
        "--adw-secondary-sidebar-fg-rgb": base16["base05"],
        "--adw-secondary-sidebar-backdrop-rgb": base16["base01"],
        "--adw-card-bg-rgb": base16["base00"],
        "--adw-card-fg-rgb": base16["base05"],
        "--adw-dialog-bg-rgb": base16["base00"],
        "--adw-dialog-fg-rgb": base16["base05"],
        "--adw-popover-bg-rgb": base16["base00"],
        "--adw-popover-fg-rgb": base16["base05"],
        "--adw-thumbnail-bg-rgb": base16["base00"],
    }
    replaced = set()
    report = []
    lines = contents.splitlines(keepends=True)
    new_lines = []

    for line in lines:
        matched = False
        for name, hex_color in targets.items():
            if re.match(rf"^\s*{re.escape(name)}\s*:", line):
                rgb = hex_to_rgb(hex_color)
                if not rgb:
                    new_lines.append(line)
                    matched = True
                    break
                r, g, b = rgb
                new_line, count = re.subn(
                    rf"^(\s*{re.escape(name)}\s*:\s*)\d+\s*,\s*\d+\s*,\s*\d+",
                    lambda m: f"{m.group(1)}{r}, {g}, {b}",
                    line,
                )
                if count:
                    replaced.add(name)
                    report.append(f"{name} -> {hex_color} ({r}, {g}, {b})")
                new_lines.append(new_line)
                matched = True
                break
        if matched:
            continue
        new_lines.append(line)

    missing = [name for name in targets.keys() if name not in replaced]
    if missing:
        report.append("missing keys: " + ", ".join(missing))

    return "".join(new_lines), report


def update_aether_zed(contents, palette):
    base16 = palette["base16"]
    ansi = palette["ansi"]
    data = json.loads(contents)
    report = []

    theme = data.get("themes", [{}])[0]
    style = theme.get("style", {})

    style_updates = {
        "border": base16["base01"],
        "border.variant": base16["base01"],
        "elevated_surface.background": base16["base00"],
        "surface.background": base16["base00"],
        "background": base16["base00"],
        "element.background": base16["base01"],
        "element.hover": base16["base02"],
        "element.selected": base16["base02"],
        "drop_target.background": base16["base02"],
        "ghost_element.hover": base16["base01"],
        "ghost_element.selected": base16["base02"],
        "text": base16["base05"],
        "text.muted": base16["base04"],
        "text.placeholder": base16["base04"],
        "text.disabled": base16["base03"],
        "text.accent": base16["base0D"],
        "status_bar.background": base16["base00"],
        "title_bar.background": base16["base00"],
        "title_bar.inactive_background": base16["base01"],
        "toolbar.background": base16["base00"],
        "tab_bar.background": base16["base00"],
        "tab.inactive_background": base16["base01"],
        "tab.active_background": base16["base00"],
        "search.match_background": base16["base02"],
        "panel.background": base16["base00"],
        "panel.focused_border": base16["base0D"],
        "scrollbar.thumb.background": base16["base02"],
        "scrollbar.thumb.hover_background": base16["base03"],
        "scrollbar.track.background": base16["base00"],
        "editor.foreground": base16["base05"],
        "editor.background": base16["base00"],
        "editor.gutter.background": base16["base00"],
        "editor.subheader.background": base16["base00"],
        "editor.active_line.background": base16["base01"],
        "editor.line_number": base16["base03"],
        "editor.active_line_number": base16["base05"],
        "editor.wrap_guide": base16["base02"],
        "editor.active_wrap_guide": base16["base02"],
        "editor.document_highlight.read_background": base16["base01"],
        "editor.document_highlight.write_background": base16["base01"],
        "terminal.background": base16["base00"],
        "terminal.foreground": base16["base05"],
        "terminal.bright_foreground": base16["base07"],
        "terminal.dim_foreground": base16["base04"],
        "link_text.hover": base16["base0C"],
        "conflict": base16["base0A"],
        "conflict.background": base16["base00"],
        "conflict.border": base16["base0A"],
        "created": base16["base0B"],
        "created.background": base16["base00"],
        "created.border": base16["base0B"],
        "deleted": base16["base08"],
        "deleted.background": base16["base00"],
        "deleted.border": base16["base08"],
        "error": base16["base08"],
        "error.background": base16["base00"],
        "error.border": base16["base08"],
        "hidden": base16["base03"],
        "hidden.background": base16["base00"],
        "hidden.border": base16["base03"],
        "hint": base16["base0C"],
        "hint.background": base16["base00"],
        "hint.border": base16["base0C"],
        "ignored": base16["base03"],
        "ignored.background": base16["base00"],
        "ignored.border": base16["base03"],
        "info": base16["base0C"],
        "info.background": base16["base00"],
        "info.border": base16["base0C"],
        "modified": base16["base0D"],
        "modified.background": base16["base00"],
        "modified.border": base16["base0D"],
        "predictive": base16["base03"],
        "predictive.background": base16["base01"],
        "predictive.border": base16["base01"],
        "renamed": base16["base09"],
        "renamed.background": base16["base00"],
        "renamed.border": base16["base09"],
        "success": base16["base0B"],
        "success.background": base16["base00"],
        "success.border": base16["base0B"],
        "unreachable": base16["base09"],
        "unreachable.background": base16["base00"],
        "unreachable.border": base16["base09"],
        "warning": base16["base09"],
        "warning.background": base16["base00"],
        "warning.border": base16["base09"],
    }

    for key, value in style_updates.items():
        if key in style:
            style[key] = value
            report.append(f"style.{key} -> {value}")
        else:
            report.append(f"missing style.{key}")

    if "scrollbar.thumb.border" in style:
        style["scrollbar.thumb.border"] = f"{base16['base03']}6f"
        report.append(f"style.scrollbar.thumb.border -> {base16['base03']}6f")
    else:
        report.append("missing style.scrollbar.thumb.border")

    terminal_map = {
        "terminal.ansi.black": ansi[0],
        "terminal.ansi.red": ansi[1],
        "terminal.ansi.green": ansi[2],
        "terminal.ansi.yellow": ansi[3],
        "terminal.ansi.blue": ansi[4],
        "terminal.ansi.magenta": ansi[5],
        "terminal.ansi.cyan": ansi[6],
        "terminal.ansi.white": ansi[7],
        "terminal.ansi.bright_black": ansi[8],
        "terminal.ansi.bright_red": ansi[9],
        "terminal.ansi.bright_green": ansi[10],
        "terminal.ansi.bright_yellow": ansi[11],
        "terminal.ansi.bright_blue": ansi[12],
        "terminal.ansi.bright_magenta": ansi[13],
        "terminal.ansi.bright_cyan": ansi[14],
        "terminal.ansi.bright_white": ansi[15],
    }
    for key, value in terminal_map.items():
        if key in style:
            style[key] = value
            report.append(f"style.{key} -> {value}")
        else:
            report.append(f"missing style.{key}")

    players = style.get("players", [])
    for idx, player in enumerate(players):
        if "cursor" in player:
            player["cursor"] = base16["base05"]
            report.append(f"players[{idx}].cursor -> {base16['base05']}")
        else:
            report.append(f"missing players[{idx}].cursor")
        if "selection" in player:
            player["selection"] = base16["base02"]
            report.append(f"players[{idx}].selection -> {base16['base02']}")
        else:
            report.append(f"missing players[{idx}].selection")

    syntax = style.get("syntax", {})
    syntax_updates = {
        "attribute": base16["base0D"],
        "boolean": base16["base09"],
        "comment": base16["base03"],
        "comment.doc": base16["base03"],
        "constant": base16["base09"],
        "constructor": base16["base0D"],
        "emphasis": base16["base0D"],
        "emphasis.strong": base16["base08"],
        "function": base16["base0D"],
        "keyword": base16["base0E"],
        "label": base16["base0A"],
        "link_text": base16["base0D"],
        "link_uri": base16["base0D"],
        "number": base16["base09"],
        "punctuation": base16["base05"],
        "punctuation.bracket": base16["base05"],
        "punctuation.delimiter": base16["base05"],
        "punctuation.list_marker": base16["base05"],
        "punctuation.special": base16["base05"],
        "string": base16["base0B"],
        "string.escape": base16["base0C"],
        "string.regex": base16["base0C"],
        "string.special": base16["base0C"],
        "string.special.symbol": base16["base0C"],
        "tag": base16["base0A"],
        "text.literal": base16["base0B"],
        "title": base16["base0D"],
        "type": base16["base0A"],
        "variable": base16["base08"],
        "variable.special": base16["base08"],
    }

    for key, value in syntax_updates.items():
        entry = syntax.get(key)
        if isinstance(entry, dict) and "color" in entry:
            entry["color"] = value
            report.append(f"syntax.{key} -> {value}")
        else:
            report.append(f"missing syntax.{key}")

    output = json.dumps(data, indent=2, ensure_ascii=True)
    if not output.endswith("\n"):
        output += "\n"

    return output, report


def apply_file(path, update_fn, palette):
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    updated, report = update_fn(original, palette)

    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)

    return report


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Apply Base16 scheme to theme files.")
    parser.add_argument("-s", "--scheme", required=True, help="Path to Base16 YAML scheme")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress per-file reporting")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    base16 = load_base16(args.scheme)
    palette = build_palette(base16)

    project_root = os.getcwd()
    ghostty_path = os.path.join(project_root, "ghostty.conf")
    neovim_path = os.path.join(project_root, "neovim.lua")
    alacritty_path = os.path.join(project_root, "alacritty.toml")
    kitty_path = os.path.join(project_root, "kitty.conf")
    warp_path = os.path.join(project_root, "warp.yaml")
    colors_fish_path = os.path.join(project_root, "colors.fish")
    fzf_path = os.path.join(project_root, "fzf.fish")
    vencord_path = os.path.join(project_root, "vencord.theme.css")
    hyprland_path = os.path.join(project_root, "hyprland.conf")
    hyprlock_path = os.path.join(project_root, "hyprlock.conf")
    mako_path = os.path.join(project_root, "mako.ini")
    waybar_path = os.path.join(project_root, "waybar.css")
    wofi_path = os.path.join(project_root, "wofi.css")
    walker_path = os.path.join(project_root, "walker.css")
    swayosd_path = os.path.join(project_root, "swayosd.css")
    btop_path = os.path.join(project_root, "btop.theme")
    cava_path = os.path.join(project_root, "cava_theme")
    chromium_path = os.path.join(project_root, "chromium.theme")
    gtk_path = os.path.join(project_root, "gtk.css")
    aether_override_path = os.path.join(project_root, "aether.override.css")
    steam_path = os.path.join(project_root, "steam.css")
    zed_path = os.path.join(project_root, "aether.zed.json")

    reports = [
        (ghostty_path, apply_file(ghostty_path, update_ghostty, palette)),
        (neovim_path, apply_file(neovim_path, update_neovim, palette)),
        (alacritty_path, apply_file(alacritty_path, update_alacritty, palette)),
        (kitty_path, apply_file(kitty_path, update_kitty, palette)),
        (warp_path, apply_file(warp_path, update_warp, palette)),
        (colors_fish_path, apply_file(colors_fish_path, update_colors_fish, palette)),
        (fzf_path, apply_file(fzf_path, update_fzf_fish, palette)),
        (vencord_path, apply_file(vencord_path, update_vencord, palette)),
        (hyprland_path, apply_file(hyprland_path, update_hyprland, palette)),
        (hyprlock_path, apply_file(hyprlock_path, update_hyprlock, palette)),
        (mako_path, apply_file(mako_path, update_mako, palette)),
        (waybar_path, apply_file(waybar_path, update_waybar, palette)),
        (wofi_path, apply_file(wofi_path, update_wofi, palette)),
        (walker_path, apply_file(walker_path, update_walker, palette)),
        (swayosd_path, apply_file(swayosd_path, update_swayosd, palette)),
        (btop_path, apply_file(btop_path, update_btop, palette)),
        (cava_path, apply_file(cava_path, update_cava, palette)),
        (chromium_path, apply_file(chromium_path, update_chromium, palette)),
        (gtk_path, apply_file(gtk_path, update_gtk_css, palette)),
        (aether_override_path, apply_file(aether_override_path, update_aether_override, palette)),
        (steam_path, apply_file(steam_path, update_steam, palette)),
        (zed_path, apply_file(zed_path, update_aether_zed, palette)),
    ]

    if not args.quiet:
        for path, report in reports:
            print(f"==> {os.path.basename(path)}")
            if report:
                for entry in report:
                    print(f"  - {format_report_line(entry)}")
            else:
                print("  - no matches")

        print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


def main_cli():
    return sys.exit(main(sys.argv[1:]))
