#!/usr/bin/env bash
set -e

# Claude Usage Widget - auto-installer
# Requer apenas Python 3.8+ (sem dependências externas)

MIN_PYTHON=308  # 3.8

check_python() {
  for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
      ver=$("$cmd" -c "import sys; print(sys.version_info.major*100+sys.version_info.minor)" 2>/dev/null || echo 0)
      if [ "$ver" -ge "$MIN_PYTHON" ] 2>/dev/null; then
        echo "$cmd"
        return
      fi
    fi
  done
  echo ""
}

PY=$(check_python)

if [ -z "$PY" ]; then
  echo ""
  echo "  ❌  Python 3.8+ não encontrado."
  echo ""
  echo "  Instale com:"
  echo "    macOS:  brew install python"
  echo "    Ubuntu: sudo apt install python3"
  echo "    Windows: https://python.org/downloads"
  echo ""
  exit 1
fi

echo ""
echo "  ✓ Python: $($PY --version)"
echo "  Iniciando Claude Usage Widget..."
echo ""

"$PY" "$(dirname "$0")/claude_usage.py"
