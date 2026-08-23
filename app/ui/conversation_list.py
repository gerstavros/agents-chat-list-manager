from __future__ import annotations

import tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk

from ..i18n import _
from ..models import ConversationMeta

_COLUMNS = ("tool", "project", "title", "updated", "messages")


class ConversationListPanel(ttk.Frame):
    def __init__(self, parent, on_select, on_delete, on_export, on_refresh):
        super().__init__(parent)
        self._on_select = on_select
        self._on_delete = on_delete
        self._on_export = on_export
        self._on_refresh = on_refresh

        self._all: list[ConversationMeta] = []
        self._filtered: list[ConversationMeta] = []
        self._meta_by_iid: dict[str, ConversationMeta] = {}
        self._tool_display_to_id: dict[str, str] = {}
        self._sort_col = "updated"
        self._sort_desc = True

        self._build_widgets()

    def _build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=4, pady=4)

        ttk.Label(toolbar, text=_("toolbar.search_placeholder")).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_args: self._apply_filters())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=24)
        search_entry.pack(side="left", padx=(0, 4))

        self.tool_var = tk.StringVar(value=_("toolbar.tool_all"))
        self.tool_combo = ttk.Combobox(toolbar, textvariable=self.tool_var, state="readonly", width=16)
        self.tool_combo.pack(side="left", padx=4)
        self.tool_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_filters())

        self.date_var = tk.StringVar(value=_("toolbar.date_all"))
        self.date_combo = ttk.Combobox(
            toolbar,
            textvariable=self.date_var,
            state="readonly",
            width=14,
            values=[_("toolbar.date_all"), _("toolbar.date_7d"), _("toolbar.date_30d")],
        )
        self.date_combo.pack(side="left", padx=4)
        self.date_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_filters())

        ttk.Button(toolbar, text=_("toolbar.refresh"), command=self._on_refresh).pack(side="left", padx=4)
        ttk.Button(toolbar, text=_("toolbar.delete"), command=self._handle_delete).pack(side="left", padx=4)
        ttk.Button(toolbar, text=_("toolbar.export"), command=self._handle_export).pack(side="left", padx=4)

        self.tree = ttk.Treeview(self, columns=_COLUMNS, show="headings", selectmode="browse")
        for col in _COLUMNS:
            self.tree.heading(col, text=_(f"column.{col}"), command=lambda c=col: self._sort_by(c))
            width = 90 if col in ("tool", "updated", "messages") else 220
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)

    def set_tool_options(self, display_to_id: dict[str, str]) -> None:
        self._tool_display_to_id = display_to_id
        all_label = _("toolbar.tool_all")
        self.tool_combo["values"] = [all_label] + list(display_to_id.keys())
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
