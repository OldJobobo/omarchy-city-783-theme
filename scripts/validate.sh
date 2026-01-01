#!/usr/bin/env bash
set -euo pipefail

scheme_path="${1:-city-783.yaml}"
python3 "$(dirname "$0")/apply-theme.py" --scheme "$scheme_path" --validate
