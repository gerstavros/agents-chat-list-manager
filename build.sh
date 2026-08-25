#!/usr/bin/env bash
# Builds a standalone single-file desktop binary (dist/agentchatmanager) for
# the current platform/architecture. PyInstaller does not cross-compile: run
# this script on the same OS/arch you intend to run the app on (e.g. a Linux
# x86_64 desktop produces a Linux x86_64 binary).
set -euo pipefail
cd "$(dirname "$0")"

# The app is a Tkinter GUI: fail fast with an actionable hint if the system
# Python can't import tkinter (PyInstaller's tkinter hook would fail later
# anyway, deep inside the build, with a less obvious error).
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "error: python3 cannot import tkinter." >&2
    echo "Install the OS package for your distro, e.g.:" >&2
    echo "  Debian/Ubuntu: sudo apt install python3-tk" >&2
    echo "  Arch/Manjaro:  sudo pacman -S tk" >&2
    echo "  Fedora:        sudo dnf install python3-tkinter" >&2
    exit 1
fi

if [ ! -d .buildenv ]; then
    python3 -m venv .buildenv
fi
source .buildenv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements-build.txt

# PyInstaller's --add-data separator is ';' on Windows, ':' everywhere else.
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows*) DATA_SEP=";" ;;
    *) DATA_SEP=":" ;;
esac

python -m PyInstaller --onefile --windowed --name agentchatmanager --clean --noconfirm \
    --add-data "locales${DATA_SEP}locales" \
    --add-data "app/ui/matrix_theme.json${DATA_SEP}app/ui" \
    --hidden-import app.adapters.claude_code \
    --hidden-import app.adapters.qwen_code \
    --hidden-import app.adapters.codewhale_tui \
    --hidden-import app.adapters.opencode \
    --hidden-import app.adapters.zed \
    --hidden-import PIL._imagingtk \
    --hidden-import PIL._tkinter_finder \
    main.py

echo
echo "Built: dist/agentchatmanager"
file dist/agentchatmanager 2>/dev/null || true
