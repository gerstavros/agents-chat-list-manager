# Agents Chat List Manager

A cross-platform (Only linux version is currently tested) desktop app (Python + Tkinter) that lists, searches, views, exports, and deletes conversation history from multiple AI coding CLI tools in one place:

- **Claude Code** (`~/.claude`)
- **Qwen Code** (`~/.qwen`, or `$QWEN_HOME`)
- **codewhale-tui** (`~/.codewhale`, or `$CODEWHALE_HOME`)
- **opencode** (`~/.local/share/opencode`, or `$OPENCODE_DATA`; a SQLite database, not JSON files)
- **Zed** (`~/.local/share/zed/threads/threads.db`, or `--zed-dir`/Settings override; SQLite with zstd-compressed thread JSON — transcripts need `libzstd` or the `zstd` CLI, metadata works without)

Storage locations are auto-detected but fully overridable per tool from the in-app **Settings** dialog.

## Requirements

- Python 3.10+
- Tkinter — bundled with the standard CPython installer on Windows and macOS. On
  minimal Linux installs it may need a separate OS package (not a `pip` package):
  - Debian/Ubuntu: `sudo apt install python3-tk`
  - Arch/Manjaro: `sudo pacman -S tk`
  - Fedora: `sudo dnf install python3-tkinter`

No third-party Python packages are required — everything runs from the standard
library.

## Running from source code

```bash
python3 main.py
```

## Building the binary

```bash
./build.sh
```

This creates a local build venv (`.buildenv/`, gitignored), installs
PyInstaller into it, and produces `dist/agentchatmanager` — a single-file
executable of the Tkinter desktop app. The build needs a working Tkinter in
the system Python (see Requirements above — e.g. `sudo pacman -S tk` on Arch).

**PyInstaller does not cross-compile.** Build on the same OS/architecture you
plan to run the app on. The resulting binary links against the build
machine's glibc, so older-glibc targets need the build done there (or in a
matching container) — same caveat as the CLI sibling.

## Features

- Merged conversation list across all configured tools, with columns for tool,
  project, title, last updated, and message count.
- Search (title/project substring), filter by tool, filter by relative date range,
  sortable columns.
- Read-only transcript viewer with a "show raw JSON" toggle per message.
- Delete a conversation (with confirmation) — removes the underlying file(s).
- Export a conversation to `.md` or `.txt`.
- Settings dialog: view auto-detected storage path per tool, override it with a
  folder picker, or reset to default. Also selects the UI language.

## Adding support for another tool

1. Create `app/adapters/your_tool.py` implementing the `ToolAdapter` interface
   (see `app/adapters/base.py`): `default_base_dir()`, `list_conversations()`,
   `load_conversation()`, `delete_conversation()`.
2. Decorate the class with `@register` (from `app.registry`).

#### Then the adapter is auto-discovered at startup and shows up in the conversation list, filters, and Settings dialog with no else changes.

## Configuration

App settings (language, per-tool path overrides) are stored at:

- Linux: `~/.config/agentchatmanager/config.json` (or `$XDG_CONFIG_HOME`)
- macOS: `~/Library/Application Support/agentchatmanager/config.json`
- Windows: `%APPDATA%\agentchatmanager\config.json`

Logs are written alongside the config file, as `agentchatmanager.log`.

## Testing

```bash
python3 -m unittest discover -s tests -v
```

Tests run only on test files under `tests/fixtures/` (and synthetic SQLite
`opencode.db` / `threads.db` databases built in temp dirs for the opencode and
Zed adapters) — they never touch your real `~/.claude`, `~/.qwen`,
`~/.codewhale`, `~/.local/share/opencode`, or `~/.local/share/zed` data.

## Internationalization

Only English (`locales/en.json`) ships today. Adding a language is a drop-in file:
copy `locales/en.json` to `locales/xx.json` and translate the values — it appears
automatically in the Settings language picker.
