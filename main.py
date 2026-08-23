from __future__ import annotations

import tkinter as tk

from app import i18n
from app.config import AppConfig
from app.logging_setup import setup_logging
from app.ui.main_window import MainWindow


def main() -> None:
    setup_logging()
    config = AppConfig.load()
    i18n.load_locale(config.language)

    root = tk.Tk()
    MainWindow(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
