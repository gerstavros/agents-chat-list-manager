from __future__ import annotations

import sys
import tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk

import customtkinter as ctk

from ..i18n import _
from ..models import ConversationMeta
from ._ctk_theme import TREEVIEW_STYLE, apply_ttk_theme
from .icons import Tooltip, gear_icon, refresh_icon, trash_icon

_COLUMNS = ("tool", "project", "title", "updated", "messages")


class ConversationListPanel(ctk.CTkFrame):
    def __init__(self, parent, on_select, on_delete, on_export, on_refresh, on_settings):
        super().__init__(parent)
        self._on_select = on_select
        self._on_delete = on_delete
        self._on_export = on_export
        self._on_refresh = on_refresh
        self._on_settings = on_settings

        self._all: list[ConversationMeta] = []
        self._filtered: list[ConversationMeta] = []
        self._meta_by_iid: dict[str, ConversationMeta] = {}
        self._tool_display_to_id: dict[str, str] = {}
        self._sort_col = "updated"
        self._sort_desc = True

        self._build_widgets()

    def _build_widgets(self) -> None:
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self._apply_filters())
        search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            width=180,
            placeholder_text=_("toolbar.search_placeholder"),
        )
        search_entry.pack(side="left", padx=(0, 6))

        self.tool_var = tk.StringVar(value=_("toolbar.tool_all"))
        self.tool_combo = ctk.CTkComboBox(
            toolbar,
            variable=self.tool_var,
            state="readonly",
            width=170,
            values=[_("toolbar.tool_all")],
            command=lambda _choice: self._apply_filters(),
        )
        self.tool_combo.pack(side="left", padx=6)

        self.date_var = tk.StringVar(value=_("toolbar.date_all"))
        self.date_combo = ctk.CTkComboBox(
            toolbar,
            variable=self.date_var,
            state="readonly",
            width=140,
            values=[_("toolbar.date_all"), _("toolbar.date_7d"), _("toolbar.date_30d")],
            command=lambda _choice: self._apply_filters(),
        )
        self.date_combo.pack(side="left", padx=6)

        refresh_btn = ctk.CTkButton(
            toolbar, image=refresh_icon(), text="", width=38, command=self._on_refresh
        )
        refresh_btn.pack(side="left", padx=4)
        Tooltip(refresh_btn, _("toolbar.refresh"))

        delete_btn = ctk.CTkButton(
            toolbar, image=trash_icon(), text="", width=38, command=self._handle_delete
        )
        delete_btn.pack(side="left", padx=4)
        Tooltip(delete_btn, _("toolbar.delete"))

        ctk.CTkButton(toolbar, text=_("toolbar.export"), width=90, command=self._handle_export).pack(
            side="left", padx=4
        )
        settings_btn = ctk.CTkButton(
            toolbar, image=gear_icon(), text="", width=38, command=self._on_settings
        )
        settings_btn.pack(side="left", padx=4)
        Tooltip(settings_btn, _("toolbar.settings"))

        # CustomTkinter has no table widget; keep ttk.Treeview, styled to match.
        self.tree = ttk.Treeview(self, columns=_COLUMNS, show="headings", selectmode="browse")
        self.tree.configure(style=TREEVIEW_STYLE)
        apply_ttk_theme(self)
        for col in _COLUMNS:
            self.tree.heading(
                col,
                text=_(f"column.{col}"),
                command=lambda c=col: self._sort_by(c),
            )
            width = 90 if col in ("tool", "updated", "messages") else 220
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)
        self._build_context_menu()

    def _build_context_menu(self) -> None:
        """Right-click menu on the conversation table (Delete / Export;
        Rename will be added later). Styled with the matrix palette — the
        classic tk.Menu has no CustomTkinter equivalent."""
        self._context_menu = tk.Menu(
            self,
            tearoff=0,
            bg="#001400",
            fg="#00FF00",
            activebackground="#003B00",
            activeforeground="#00FF00",
            bd=0,
            relief="flat",
            font=("TkDefaultFont", 10),
        )
        self._context_menu.add_command(label=_("toolbar.delete"), command=self._handle_delete)
        self._context_menu.add_command(label=_("toolbar.export"), command=self._handle_export)
        self.tree.bind("<Button-3>", self._on_context_menu)
        if sys.platform == "darwin":
            self.tree.bind("<Button-2>", self._on_context_menu)

    def _on_context_menu(self, event) -> None:
        row = self.tree.identify_row(event.y)
        if not row:
            return
        # Right-click selects the row under the cursor first (standard UX).
        if row not in self.tree.selection():
            self.tree.selection_set(row)
            self.tree.focus(row)
            self._on_select(self.get_selected())
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def set_tool_options(self, display_to_id: dict[str, str]) -> None:
        self._tool_display_to_id = display_to_id
        all_label = _("toolbar.tool_all")
        self.tool_combo.configure(values=[all_label] + list(display_to_id.keys()))
        self.tool_var.set(all_label)

    def set_data(self, convs: list[ConversationMeta]) -> None:
        self._all = convs
        self._apply_filters()

    def get_selected(self) -> ConversationMeta | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self._meta_by_iid.get(selection[0])

    def _apply_filters(self) -> None:
        query = self.search_var.get().strip().lower()
        selected_tool_label = self.tool_var.get()
        tool_id = self._tool_display_to_id.get(selected_tool_label)
        date_choice = self.date_var.get()
        now = datetime.now(timezone.utc)

        filtered = []
        for conv in self._all:
            if tool_id and conv.tool_id != tool_id:
                continue
            if query and query not in conv.title.lower() and query not in conv.project_path.lower():
                continue
            if date_choice == _("toolbar.date_7d") and not self._within_days(conv.updated_at, 7, now):
                continue
            if date_choice == _("toolbar.date_30d") and not self._within_days(conv.updated_at, 30, now):
                continue
            filtered.append(conv)
        self._filtered = filtered
        self._sort_and_render()

    @staticmethod
    def _within_days(dt: datetime | None, days: int, now: datetime) -> bool:
        if dt is None:
            return False
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (now - dt).days <= days

    def _sort_and_render(self) -> None:
        min_dt = datetime.min.replace(tzinfo=timezone.utc)
        key_funcs = {
            "tool": lambda c: c.tool_id,
            "project": lambda c: c.project_path.lower(),
            "title": lambda c: c.title.lower(),
            "updated": lambda c: c.updated_at or min_dt,
            "messages": lambda c: c.message_count,
        }
        keyfunc = key_funcs.get(self._sort_col, key_funcs["updated"])
        items = sorted(self._filtered, key=keyfunc, reverse=self._sort_desc)

        selected_iid = None
        selection = self.tree.selection()
        if selection:
            selected_iid = selection[0]

        self.tree.delete(*self.tree.get_children())
        self._meta_by_iid.clear()
        for conv in items:
            display_tool = _(f"tool.{conv.tool_id}")
            updated_str = conv.updated_at.strftime("%Y-%m-%d %H:%M") if conv.updated_at else ""
            self.tree.insert(
                "", "end", iid=conv.iid,
                values=(display_tool, conv.project_path, conv.title, updated_str, conv.message_count),
            )
            self._meta_by_iid[conv.iid] = conv

        if selected_iid and selected_iid in self._meta_by_iid:
            self.tree.selection_set(selected_iid)

    def _sort_by(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = True
        self._sort_and_render()

    def _handle_select(self, _event) -> None:
        self._on_select(self.get_selected())

    def _handle_delete(self) -> None:
        meta = self.get_selected()
        if meta is not None:
            self._on_delete(meta)

    def _handle_export(self) -> None:
        meta = self.get_selected()
        if meta is not None:
            self._on_export(meta)
