from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from .. import i18n
from ..config import AppConfig
from ..i18n import _
from ..registry import get_adapter_classes


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config: AppConfig, on_save: Callable[[], None]):
        super().__init__(parent)
        self.title(_("settings.title"))
        self.resizable(False, False)
        self._config = config
        self._on_save = on_save
        self._path_vars: dict[str, tuple[tk.StringVar, type]] = {}
        self._status_labels: dict[str, ctk.CTkLabel] = {}

        self._build_widgets()

        self.transient(parent)
        self.grab_set()

    def _build_widgets(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        headers = [_("settings.tool_column"), _("settings.path_column"), _("settings.status_column"), "", ""]
        for col, text in enumerate(headers):
            ctk.CTkLabel(frame, text=text, font=("TkDefaultFont", 11, "bold")).grid(
                row=0, column=col, sticky="w", padx=6, pady=(0, 6)
            )

        classes = get_adapter_classes()
        row = 1
        for cls in classes:
            display = _(cls.display_name_key)
            override = self._config.path_overrides.get(cls.tool_id)
            current_path = override or str(cls.default_base_dir())

            ctk.CTkLabel(frame, text=display).grid(row=row, column=0, sticky="w", padx=6, pady=3)

            var = tk.StringVar(value=current_path)
            self._path_vars[cls.tool_id] = (var, cls)
            # Editable path entry: typing (or Browse/Reset) updates the status
            # label live, and _save() turns any non-default value into an override.
            var.trace_add(
                "write", lambda *_a, t=cls.tool_id, d=current_path: self._update_status(t, d)
            )
            ctk.CTkEntry(frame, textvariable=var, width=440).grid(
                row=row, column=1, sticky="we", padx=6, pady=3
            )

            status_label = ctk.CTkLabel(frame, text=self._status_text(current_path, override))
            status_label.grid(row=row, column=2, sticky="w", padx=6, pady=3)
            self._status_labels[cls.tool_id] = status_label

            ctk.CTkButton(frame, text=_("settings.browse"), width=80, command=lambda c=cls: self._browse(c)).grid(
                row=row, column=3, padx=4, pady=3
            )
            ctk.CTkButton(frame, text=_("settings.reset"), width=80, command=lambda c=cls: self._reset(c)).grid(
                row=row, column=4, padx=4, pady=3
            )
            row += 1

        ctk.CTkLabel(frame, text=_("settings.appearance")).grid(row=row, column=0, sticky="w", pady=(14, 3))
        self._appearance_var = tk.StringVar(
            value=_("settings.appearance_dark")
            if self._config.appearance == "dark"
            else _("settings.appearance_light")
        )
        ctk.CTkComboBox(
            frame,
            variable=self._appearance_var,
            values=[_("settings.appearance_dark"), _("settings.appearance_light")],
            state="readonly",
            width=110,
        ).grid(row=row, column=1, sticky="w", pady=(14, 3))

        row += 1
        ctk.CTkLabel(frame, text=_("settings.language")).grid(row=row, column=0, sticky="w", pady=(14, 3))
        self._lang_var = tk.StringVar(value=self._config.language)
        ctk.CTkComboBox(
            frame,
            variable=self._lang_var,
            values=i18n.available_locales(),
            state="readonly",
            width=90,
        ).grid(row=row, column=1, sticky="w", pady=(14, 3))

        button_row = ctk.CTkFrame(self)
        button_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(button_row, text=_("settings.save"), width=100, command=self._save).pack(
            side="right", padx=(4, 0)
        )
        ctk.CTkButton(button_row, text=_("settings.cancel"), width=100, command=self.destroy).pack(
            side="right"
        )

    @staticmethod
    def _status_text(path_str: str, has_override: str | None) -> str:
        if not Path(path_str).exists():
            return _("settings.status_missing")
        return _("settings.status_custom") if has_override else _("settings.status_auto")

    def _update_status(self, tool_id: str, default_path: str) -> None:
        var, _cls = self._path_vars[tool_id]
        current = var.get()
        override = None if current == default_path else current
        self._status_labels[tool_id].configure(text=self._status_text(current, override))

    def _browse(self, cls: type) -> None:
        display = _(cls.display_name_key)
        chosen = filedialog.askdirectory(
            parent=self, title=_("settings.browse_dialog_title", tool=display)
        )
        if not chosen:
            return
        var, _cls = self._path_vars[cls.tool_id]
        var.set(chosen)  # trace updates the status label

    def _reset(self, cls: type) -> None:
        var, _cls = self._path_vars[cls.tool_id]
        var.set(str(cls.default_base_dir()))  # trace updates the status label

    def _save(self) -> None:
        for tool_id, (var, cls) in self._path_vars.items():
            path_val = var.get()
            default_path = str(cls.default_base_dir())
            override = None if path_val == default_path else path_val
            self._config.set_path_override(tool_id, override)
        self._config.appearance = (
            "dark" if self._appearance_var.get() == _("settings.appearance_dark") else "light"
        )
        self._config.language = self._lang_var.get()
        self._config.save()
        self._on_save()
        self.destroy()
