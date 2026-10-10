#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [[ -n "${NFTPZ_PYTHON:-}" ]]; then
  PYTHON="$NFTPZ_PYTHON"
elif [[ -x /opt/homebrew/opt/python@3.12/bin/python3.12 && -d "$ROOT/.runtime/python312" ]]; then
  PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12
else
  PYTHON=python
fi
if [[ -d "$ROOT/.runtime/python312" ]]; then
  export PYTHONPATH="$ROOT/.runtime/python312:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi
exec "$PYTHON" -m nftpz_platform "$@"
