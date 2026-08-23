from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from ..i18n import _
from ..models import ConversationMeta, Message

_ROLE_TAGS = {
    "user": "role_user",
    "assistant": "role_assistant",
    "system": "role_system",
}


class TranscriptViewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._messages: list[Message] = []
        self._meta: ConversationMeta | None = None
        self._raw_var = tk.BooleanVar(value=False)
        self._build_widgets()

    def _build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=4, pady=4)
        ttk.Checkbutton(
            toolbar, text=_("transcript.raw_toggle"), variable=self._raw_var, command=self._render
        ).pack(side="left")

        self.status_label = ttk.Label(self, text=_("status.no_selection"), anchor="w")
        self.status_label.pack(fill="x", padx=4)

        self.text = ScrolledText(self, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, padx=4, pady=4)
        self.text.tag_configure("role_user", foreground="#2b6cb0")
        self.text.tag_configure("role_assistant", foreground="#2f855a")
        self.text.tag_configure("role_system", foreground="#805ad5")
        self.text.tag_configure("meta", foreground="#718096")
        self.text.tag_configure("raw", foreground="#a0aec0", font=("Courier", 9))

    def show_loading(self) -> None:
        self.status_label.config(text=_("status.loading_conversation"))
        self._write("")

    def show_messages(self, meta: ConversationMeta, messages: list[Message]) -> None:
        self._meta = meta
        self._messages = messages
        self.status_label.config(text=meta.title)
        self._render()

    def clear(self) -> None:
        self._meta = None
        self._messages = []
        self.status_label.config(text=_("status.no_selection"))
        self._write("")

    def _render(self) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        for msg in self._messages:
            ts = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else _("transcript.no_timestamp")
            header = f"[{ts}] {msg.role}"
            if msg.has_tool_call:
                header += f" {_('transcript.tool_call_marker')}"
            role_tag = _ROLE_TAGS.get(msg.role, "meta")
            self.text.insert("end", header + "\n", ("meta",))
            self.text.insert("end", (msg.text or "") + "\n\n", (role_tag,))
            if self._raw_var.get():
                raw_str = json.dumps(msg.raw, indent=2, ensure_ascii=False)
                self.text.insert("end", raw_str + "\n\n", ("raw",))
        self.text.config(state="disabled")

    def _write(self, content: str) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", content)
        self.text.config(state="disabled")
