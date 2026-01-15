#!/usr/bin/env bash
set -euo pipefail

ws_id="${1:-}"

if [[ -z "$ws_id" ]]; then
  printf '{"text":"","class":"empty"}\n'
  exit 0
fi

if ! command -v hyprctl >/dev/null 2>&1; then
  printf '{"text":"%s","class":"empty"}\n' "$ws_id"
  exit 0
fi

active_id="$(hyprctl activeworkspace -j 2>/dev/null | jq -r '.id' 2>/dev/null || echo "")"

if hyprctl workspaces -j 2>/dev/null | jq -e --argjson id "$ws_id" '.[] | select(.id == $id)' >/dev/null 2>&1; then
  present="yes"
else
  present="no"
fi

if [[ "$active_id" == "$ws_id" ]]; then
  class="active"
elif [[ "$present" == "yes" ]]; then
  class="occupied"
else
  class="empty"
fi

printf '{"text":"%s","class":"%s"}\n' "$ws_id" "$class"
