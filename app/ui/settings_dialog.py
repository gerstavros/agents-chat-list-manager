from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable

from .. import i18n
from ..config import AppConfig
from ..i18n import _
from ..registry import get_adapter_classes


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config: AppConfig, on_save: Callable[[], None]):
        super().__init__(parent)
        self.title(_("settings.title"))
        self.resizable(False, False)
        self._config = config
        self._on_save = on_save
        self._path_vars: dict[str, tuple[tk.StringVar, type]] = {}
        self._status_labels: dict[str, ttk.Label] = {}

        self._build_widgets()

        self.transient(parent)
        self.grab_set()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        headers = [_("settings.tool_column"), _("settings.path_column"), _("settings.status_column"), "", ""]
        for col, text in enumerate(headers):
            ttk.Label(frame, text=text, font=("TkDefaultFont", 9, "bold")).grid(
                row=0, column=col, sticky="w", padx=4, pady=4
            )

        classes = get_adapter_classes()
        row = 1
        for cls in classes:
            display = _(cls.display_name_key)
            override = self._config.path_overrides.get(cls.tool_id)
            current_path = override or str(cls.default_base_dir())

            ttk.Label(frame, text=display).grid(row=row, column=0, sticky="w", padx=4, pady=2)

            var = tk.StringVar(value=current_path)
            self._path_vars[cls.tool_id] = (var, cls)
            ttk.Entry(frame, textvariable=var, width=50, state="readonly").grid(
                row=row, column=1, sticky="we", padx=4, pady=2
            )

            status_label = ttk.Label(frame, text=self._status_text(current_path, override))
            status_label.grid(row=row, column=2, sticky="w", padx=4, pady=2)
            self._status_labels[cls.tool_id] = status_label

            ttk.Button(frame, text=_("settings.browse"), command=lambda c=cls: self._browse(c)).grid(
                row=row, column=3, padx=2, pady=2
            )
            ttk.Button(frame, text=_("settings.reset"), command=lambda c=cls: self._reset(c)).grid(
                row=row, column=4, padx=2, pady=2
            )
            row += 1

        ttk.Label(frame, text=_("settings.language")).grid(row=row, column=0, sticky="w", pady=(12, 2))
        self._lang_var = tk.StringVar(value=self._config.language)
        ttk.Combobox(
            frame, textvariable=self._lang_var, values=i18n.available_locales(), state="readonly", width=10
        ).grid(row=row, column=1, sticky="w", pady=(12, 2))

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(button_row, text=_("settings.save"), command=self._save).pack(side="right", padx=(4, 0))
        ttk.Button(button_row, text=_("settings.cancel"), command=self.destroy).pack(side="right")

    @staticmethod
    def _status_text(path_str: str, has_override: str | None) -> str:
        if not Path(path_str).exists():
            return _("settings.status_missing")
        return _("settings.status_custom") if has_override else _("settings.status_auto")

    def _browse(self, cls: type) -> None:
        display = _(cls.display_name_key)
        chosen = filedialog.askdirectory(
            parent=self, title=_("settings.browse_dialog_title", tool=display)
        )
        if not chosen:
            return
        var, _cls = self._path_vars[cls.tool_id]
        var.set(chosen)
        self._status_labels[cls.tool_id].config(text=_("settings.status_custom"))

    def _reset(self, cls: type) -> None:
        var, _cls = self._path_vars[cls.tool_id]
        default_path = str(cls.default_base_dir())
        var.set(default_path)
        self._status_labels[cls.tool_id].config(text=self._status_text(default_path, None))

    def _save(self) -> None:
        for tool_id, (var, cls) in self._path_vars.items():
            path_val = var.get()
            default_path = str(cls.default_base_dir())
            override = None if path_val == default_path else path_val
            self._config.set_path_override(tool_id, override)
        self._config.language = self._lang_var.get()
        self._config.save()
        self._on_save()
        self.destroy()
