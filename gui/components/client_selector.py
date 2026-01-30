"""
Client Selector Dialog Module.

This module provides a modal dialog for selecting a client/organization
from a searchable list. Features include:
- Real-time search filtering
- Keyboard navigation (Enter to select, Escape to cancel)
- Optional result filtering toggle
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional, Dict
import unicodedata


__all__ = ["select_client", "ClientSelectorDialog"]


def _normalize(text: str) -> str:
    """
    Normalize text for user-friendly searches.

    Converts text to lowercase and removes accents/diacritics.

    Args:
        text: Text to normalize

    Returns:
        str: Normalized lowercase text without diacritics
    """
    if text is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


class ClientSelectorDialog(tk.Toplevel):
    """
    Modal popup dialog for client selection.

    Features:
    - Search field with real-time filtering
    - 'Filter results' checkbox toggle
    - Scrollable listbox for client display

    Actions:
    - Click/Enter: Select and close
    - Escape: Cancel

    Attributes:
        result (Optional[str]): Selected client ID, or None if cancelled
    """

    def __init__(
        self,
        parent: Optional[tk.Widget],
        clients: List[Tuple[str, str]],
        title: str = "Select a client",
    ):
        """
        Initialize the ClientSelectorDialog.

        Args:
            parent: Parent widget (optional). Dialog centers over parent if provided.
            clients: List of tuples (client_name, client_id)
            title: Dialog window title
        """
        super().__init__(master=parent)
        self.title(title)
        self.resizable(False, True)
        self.transient(parent)
        self.result: Optional[str] = None

        # Keep reference to original data
        # Internal structure: [{"name":..., "id":..., "norm":...}, ...]
        self._all_clients: List[Dict[str, str]] = [
            {
                "name": str(name),
                "id": str(client_id),
                "norm": _normalize(name),
            }
            for name, client_id in clients
        ]
        # Currently displayed list (indices reference this list)
        self._visible: List[Dict[str, str]] = list(self._all_clients)

        # Build UI
        self._build_widgets()

        # Make modal and center over parent
        self._make_modal(parent)
        self._center_over_parent(parent)

        # Populate initial list
        self._refresh_listbox(select_first=True)

        # Wait until window is closed
        self.wait_window(self)

    # ---------- UI Helpers ----------

    def _build_widgets(self) -> None:
        """Build and layout all dialog widgets."""
        pad = 10

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=pad, pady=pad)

        # Search bar
        top_bar = ttk.Frame(container)
        top_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(top_bar, text="Search:").pack(side="left")

        self.var_query = tk.StringVar()
        self.entry_search = ttk.Entry(top_bar, textvariable=self.var_query, width=30)
        self.entry_search.pack(side="left", padx=(6, 6))
        self.entry_search.bind("<KeyRelease>", self._on_search_change)
        self.entry_search.bind("<Return>", self._on_return_keystroke)

        self.var_filter = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(
            top_bar, text="Filter results",
            variable=self.var_filter,
            command=self._on_search_change
        )
        cb.pack(side="left")

        # Listbox + Scrollbar
        list_frame = ttk.Frame(container)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            activestyle="dotbox",
            height=12,
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Selection/close events
        self.listbox.bind("<<ListboxSelect>>", self._on_select_and_close)
        self.listbox.bind("<Double-Button-1>", self._on_select_and_close)
        self.listbox.bind("<Return>", self._on_select_and_close)

        # Button bar
        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=(6, 0))

        self.btn_ok = ttk.Button(btns, text="Accept", command=self._on_select_and_close)
        self.btn_ok.pack(side="right", padx=(6, 0))

        btn_cancel = ttk.Button(btns, text="Cancel", command=self._on_cancel)
        btn_cancel.pack(side="right")

        # Escape key cancels
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _make_modal(self, parent: Optional[tk.Widget]) -> None:
        """Make the dialog modal."""
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _center_over_parent(self, parent: Optional[tk.Widget]) -> None:
        """Center the dialog over the parent widget."""
        self.update_idletasks()
        if parent is not None:
            try:
                px = parent.winfo_rootx()
                py = parent.winfo_rooty()
                pw = parent.winfo_width()
                ph = parent.winfo_height()
                w = self.winfo_width()
                h = self.winfo_height()
                x = px + (pw - w) // 2
                y = py + (ph - h) // 2
                self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
            except Exception:
                pass
        # Set focus to search field
        self.entry_search.focus_set()

    # ---------- Data / Search ----------

    def _apply_search(self) -> None:
        """Apply the current search query to filter visible clients."""
        query = _normalize(self.var_query.get())
        if not query:
            self._visible = list(self._all_clients)
            return

        if self.var_filter.get():
            # Filter list to show only matches
            self._visible = [c for c in self._all_clients if query in c["norm"]]
        else:
            # Don't filter: keep all but select/center first match
            self._visible = list(self._all_clients)

    def _refresh_listbox(self, select_first: bool = False) -> None:
        """Refresh the listbox contents based on visible clients."""
        query = _normalize(self.var_query.get())
        self.listbox.delete(0, tk.END)

        for c in self._visible:
            self.listbox.insert(tk.END, c["name"])

        if select_first and self._visible:
            idx = 0
            if query:
                # Find first match to highlight
                for i, c in enumerate(self._visible):
                    if query in c["norm"]:
                        idx = i
                        break
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.listbox.activate(idx)

        # Enable/disable OK button
        state = tk.NORMAL if self._visible else tk.DISABLED
        self.btn_ok.config(state=state)

    # ---------- Events ----------

    def _on_search_change(self, event=None) -> None:
        """Handle search field changes."""
        self._apply_search()
        # Select first match for visual highlighting
        self._refresh_listbox(select_first=True)

    def _on_return_keystroke(self, event=None) -> None:
        """Handle Enter key in search field."""
        self._on_select_and_close()

    def _on_select_and_close(self, event=None) -> None:
        """Handle selection and close the dialog."""
        # If no visible items, do nothing
        if not self._visible:
            self.bell()
            return

        cur = self.listbox.curselection()
        if not cur:
            # If no selection yet, take the first item
            idx = 0
        else:
            idx = cur[0]

        try:
            chosen = self._visible[idx]
            self.result = chosen["id"]
        except Exception:
            self.result = None
        finally:
            self.destroy()

    def _on_cancel(self) -> None:
        """Handle cancel action."""
        self.result = None
        self.destroy()


def select_client(
    clients: List[Tuple[str, str]],
    parent: Optional[tk.Widget] = None,
    title: str = "Select a client",
) -> Optional[str]:
    """
    Open a modal popup to select a client.

    Args:
        clients: List of tuples with format [('client_name', 'client_id'), ...]
        parent: Parent widget (optional). If provided, popup centers over it.
        title: Dialog window title.

    Returns:
        Optional[str]: The selected client_id, or None if cancelled.
    """
    dlg = ClientSelectorDialog(parent=parent, clients=clients, title=title)
    return dlg.result
