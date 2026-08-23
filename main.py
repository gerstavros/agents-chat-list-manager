from __future__ import annotations

import logging
import tkinter as tk

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

    root = tk.Tk()
    MainWindow(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
