from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .. import i18n
from ..config import AppConfig
from ..export import export_conversation
from ..i18n import _
from ..models import ConversationMeta
from ..registry import build_adapters
from ..service import ConversationService
from .conversation_list import ConversationListPanel
from .settings_dialog import SettingsDialog
from .transcript_view import TranscriptViewPanel


class MainWindow:
    def __init__(self, root: tk.Tk, config: AppConfig):
        self.root = root
        self.config = config
        self.service = ConversationService(build_adapters(config))
        self._queue: "queue.Queue" = queue.Queue()

        self._build_widgets()
        self._start_queue_polling()
        self.refresh()

    def _build_widgets(self) -> None:
        self.root.title(_("app.title"))
        self.root.geometry("1100x650")

        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=_("menu.file.settings"), command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label=_("menu.file.exit"), command=self.root.quit)
        menubar.add_cascade(label=_("menu.file"), menu=file_menu)
        self.root.config(menu=menubar)

        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True)

        self.list_panel = ConversationListPanel(
            paned,
            on_select=self.on_select,
            on_delete=self.on_delete_request,
            on_export=self.on_export_request,
            on_refresh=self.refresh,
        )
        self.transcript_panel = TranscriptViewPanel(paned)
        paned.add(self.list_panel, weight=1)
        paned.add(self.transcript_panel, weight=2)

        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(fill="x", side="bottom")

        self._refresh_tool_options()

    def _refresh_tool_options(self) -> None:
        display_to_id = {_(a.display_name_key): a.tool_id for a in self.service.adapters()}
        self.list_panel.set_tool_options(display_to_id)

    def _start_queue_polling(self) -> None:
        def poll() -> None:
            try:
                while True:
                    kind, payload = self._queue.get_nowait()
                    if kind == "conversations":
                        self.list_panel.set_data(payload)
                        self.status_var.set(_("status.loaded", count=len(payload)))
                    elif kind == "messages":
                        meta, messages = payload
                        self.transcript_panel.show_messages(meta, messages)
            except queue.Empty:
                pass
            self.root.after(100, poll)

        self.root.after(100, poll)

    def refresh(self) -> None:
        self.status_var.set(_("status.scanning"))
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self) -> None:
        convs = self.service.list_all()
        self._queue.put(("conversations", convs))

    def on_select(self, meta: ConversationMeta | None) -> None:
        if meta is None:
            self.transcript_panel.clear()
            return
        self.transcript_panel.show_loading()
        threading.Thread(target=self._load_worker, args=(meta,), daemon=True).start()

    def _load_worker(self, meta: ConversationMeta) -> None:
        messages = self.service.load(meta)
        self._queue.put(("messages", (meta, messages)))

    def on_delete_request(self, meta: ConversationMeta) -> None:
        if not messagebox.askyesno(
            _("confirm.delete_title"), _("confirm.delete_message", title=meta.title)
        ):
            return
        try:
            self.service.delete(meta)
        except OSError as exc:
            messagebox.showerror(_("error.delete_title"), _("error.delete_message", error=str(exc)))
            return
        self.transcript_panel.clear()
        self.refresh()

    def on_export_request(self, meta: ConversationMeta) -> None:
        messages = self.service.load(meta)
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in meta.title)[:40].strip() or "conversation"
        path_str = filedialog.asksaveasfilename(
            parent=self.root,
            title=_("export.dialog_title"),
            defaultextension=".md",
            filetypes=[(_("export.filetype_markdown"), "*.md"), (_("export.filetype_text"), "*.txt")],
            initialfile=f"{safe_title}.md",
        )
        if not path_str:
            return
        path = Path(path_str)
        fmt = "markdown" if path.suffix.lower() == ".md" else "text"
        try:
            export_conversation(meta, messages, path, fmt)
        except OSError as exc:
            messagebox.showerror(_("error.export_title"), _("error.export_message", error=str(exc)))
            return
        messagebox.showinfo(_("export.success_title"), _("export.success_message", path=str(path)))

    def open_settings(self) -> None:
        SettingsDialog(self.root, self.config, on_save=self._on_settings_saved)

    def _on_settings_saved(self) -> None:
        i18n.load_locale(self.config.language)
        self.service = ConversationService(build_adapters(self.config))
        self._refresh_tool_options()
        self.refresh()
