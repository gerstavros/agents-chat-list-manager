from __future__ import annotations

import json
import tkinter as tk

import customtkinter as ctk

from ..i18n import _
from ..models import ConversationMeta, Message

_ROLE_TAGS = {
    "user": "role_user",
    "assistant": "role_assistant",
    "system": "role_system",
}

# Matrix green role palette per appearance mode (bright on dark, deep on light).
_ROLE_COLORS = {
    "dark": {
        "role_user": "#00FF00",
        "role_assistant": "#66FF66",
        "role_system": "#00CC66",
        "meta": "#00AA00",
        "raw": "#33AA33",
    },
    "light": {
        "role_user": "#005C00",
        "role_assistant": "#008F11",
        "role_system": "#007A5E",
        "meta": "#4E7A4E",
        "raw": "#6E8C6E",
    },
}


class TranscriptViewPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._messages: list[Message] = []
        self._meta: ConversationMeta | None = None
        self._raw_var = tk.BooleanVar(value=False)
        self._build_widgets()

    def _build_widgets(self) -> None:
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkCheckBox(
            toolbar, text=_("transcript.raw_toggle"), variable=self._raw_var, command=self._render
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(self, text=_("status.no_selection"), anchor="w")
        self.status_label.pack(fill="x", padx=8)

        self.text = ctk.CTkTextbox(self, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self.apply_appearance(ctk.get_appearance_mode().lower())

    def apply_appearance(self, appearance: str) -> None:
        """Re-apply role tag colors for the active appearance mode (called at
        build time and again when the user switches dark/light in Settings).
        CTkTextbox forbids tag-level fonts (scaling-incompatible), so the raw
        JSON tag only varies its color."""
        colors = _ROLE_COLORS.get(appearance, _ROLE_COLORS["dark"])
        for tag, color in colors.items():
            self.text.tag_config(tag, foreground=color)

    def show_loading(self) -> None:
        self.status_label.configure(text=_("status.loading_conversation"))
        self._write("")

    def show_messages(self, meta: ConversationMeta, messages: list[Message]) -> None:
        self._meta = meta
        self._messages = messages
        self.status_label.configure(text=meta.title)
        self._render()

    def clear(self) -> None:
        self._meta = None
        self._messages = []
        self.status_label.configure(text=_("status.no_selection"))
        self._write("")

    def _render(self) -> None:
        self.text.configure(state="normal")
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
        self.text.configure(state="disabled")

    def _write(self, content: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", content)
        self.text.configure(state="disabled")
