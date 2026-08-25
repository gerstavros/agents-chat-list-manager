from __future__ import annotations

import logging
from pathlib import Path

import customtkinter as ctk

from app import i18n
from app.claude_settings import ensure_claude_cleanup_period
from app.config import AppConfig
from app.logging_setup import setup_logging
from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    status = ensure_claude_cleanup_period()
    if status in ("created", "updated"):
        logger.info("Claude Code settings: %s cleanupPeriodDays", status)
    config = AppConfig.load()
    i18n.load_locale(config.language)

    # Matrix green look, dark or light per user setting (persisted in
    # AppConfig; the custom theme JSON defines both palettes). The theme path
    # is resolved relative to this file so it works from source and inside the
    # PyInstaller bundle.
    appearance = config.appearance if config.appearance in ("dark", "light") else "dark"
    ctk.set_appearance_mode(appearance)
    theme_path = Path(__file__).resolve().parent / "app" / "ui" / "matrix_theme.json"
    ctk.set_default_color_theme(str(theme_path))

    root = ctk.CTk()
    MainWindow(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
