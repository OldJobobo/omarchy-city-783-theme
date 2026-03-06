#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
THEME_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
STATE_DIR="$THEME_DIR/.cache"
STATE_FILE="$STATE_DIR/compact-mode.state"
CSS_FILE="$SCRIPT_DIR/compact-state-active.css"
NORMAL_CSS="$SCRIPT_DIR/compact-state-normal.css"
COMPACT_CSS="$SCRIPT_DIR/compact-state-compact.css"

mkdir -p "$STATE_DIR"

if [[ ! -f "$STATE_FILE" ]]; then
  printf 'normal\n' > "$STATE_FILE"
fi

current="$(tr -d '[:space:]' < "$STATE_FILE")"
if [[ "$current" == "compact" ]]; then
  printf 'normal\n' > "$STATE_FILE"
  cp "$NORMAL_CSS" "$CSS_FILE"
else
  printf 'compact\n' > "$STATE_FILE"
  cp "$COMPACT_CSS" "$CSS_FILE"
fi

pkill -RTMIN+9 waybar >/dev/null 2>&1 || true
