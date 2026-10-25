#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VIDEO="${1:-$SCRIPT_DIR/rick_edit.mp4}"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c 'import imageio_ffmpeg, PIL' >/dev/null 2>&1; then
  "$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
fi

exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/ascii_video.py" "$VIDEO" --start 4 --color --fit stretch --zoom 1.7
