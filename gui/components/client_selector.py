# client_selector.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional, Dict
import unicodedata


__all__ = ["select_client", "ClientSelectorDialog"]


def _normalize(text: str) -> str:
    """
    Normaliza texto para búsquedas 'amigables':
    - lower()
    - sin acentos/diacríticos
    """
    if text is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


class ClientSelectorDialog(tk.Toplevel):
    """
    Popup modal con:
      - campo de búsqueda
      - checkbox 'Filtrar resultados'
      - Listbox con scroll
    Acción:
      - Click/Enter selecciona y cierra
      - ESC cancela
    Atributo:
      - result: Optional[str] -> id_cliente seleccionado o None
    """

    def __init__(
        self,
        parent: Optional[tk.Widget],
        clients: List[Tuple[str, str]],
        title: str = "Select a client",
    ):
        super().__init__(master=parent)
        self.title(title)
        self.resizable(False, True)
        self.transient(parent)
        self.result: Optional[str] = None

        # Mantener referencia a datos originales
        # Estructura interna: [{"name":..., "id":..., "norm":...}, ...]
        self._all_clients: List[Dict[str, str]] = [
            {
                "name": str(name),
                "id": str(client_id),
                "norm": _normalize(name),
            }
            for name, client_id in clients
        ]
        # Lista actualmente mostrada (índices referencian esta lista)
        self._visible: List[Dict[str, str]] = list(self._all_clients)

        # ---- UI ----
        self._build_widgets()

        # Modal + centrado relativo al parent
        self._make_modal(parent)
        self._center_over_parent(parent)

        # Poblar lista inicial
        self._refresh_listbox(select_first=True)

        # Esperar hasta que la ventana se cierre
        self.wait_window(self)

    # ---------- UI helpers ----------

    def _build_widgets(self) -> None:
        pad = 10

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=pad, pady=pad)

        # Buscador
        top_bar = ttk.Frame(container)
        top_bar.pack(fill="x", pady=(0, 6))

        ttk.Label(top_bar, text="Search:").pack(side="left")

        self.var_query = tk.StringVar()
        self.entry_search = ttk.Entry(top_bar, textvariable=self.var_query, width=30)
        self.entry_search.pack(side="left", padx=(6, 6))
        self.entry_search.bind("<KeyRelease>", self._on_search_change)
        self.entry_search.bind("<Return>", self._on_return_keystroke)

        self.var_filter = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(top_bar, text="Filter results", variable=self.var_filter, command=self._on_search_change)
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

        # Eventos de selección/cierre
        # Click libera el botón -> selecciona y cierra
        self.listbox.bind("<<ListboxSelect>>", self._on_select_and_close)
        self.listbox.bind("<Double-Button-1>", self._on_select_and_close)
        self.listbox.bind("<Return>", self._on_select_and_close)

        # Botonera
        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=(6, 0))

        self.btn_ok = ttk.Button(btns, text="Accept", command=self._on_select_and_close)
        self.btn_ok.pack(side="right", padx=(6, 0))

        btn_cancel = ttk.Button(btns, text="Cancel", command=self._on_cancel)
        btn_cancel.pack(side="right")

        # Tecla ESC -> cancelar
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _make_modal(self, parent: Optional[tk.Widget]) -> None:
        self.grab_set()  # hacer modal
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _center_over_parent(self, parent: Optional[tk.Widget]) -> None:
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
        # Foco al buscador
        self.entry_search.focus_set()

    # ---------- Data / search ----------

    def _apply_search(self) -> None:
        query = _normalize(self.var_query.get())
        if not query:
            self._visible = list(self._all_clients)
            return

        if self.var_filter.get():
            # Filtrar la lista para mostrar solo coincidencias
            self._visible = [c for c in self._all_clients if query in c["norm"]]
        else:
            # No filtrar: mantener todo pero selecciona/centra primera coincidencia
            self._visible = list(self._all_clients)

    def _refresh_listbox(self, select_first: bool = False) -> None:
        query = _normalize(self.var_query.get())
        self.listbox.delete(0, tk.END)

        for c in self._visible:
            self.listbox.insert(tk.END, c["name"])

        if select_first and self._visible:
            idx = 0
            if query:
                # buscar primera coincidencia para resaltar
                for i, c in enumerate(self._visible):
                    if query in c["norm"]:
                        idx = i
                        break
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self.listbox.activate(idx)

        # Habilitar/Deshabilitar OK
        state = tk.NORMAL if self._visible else tk.DISABLED
        self.btn_ok.config(state=state)

    # ---------- Events ----------

    def _on_search_change(self, event=None) -> None:
        self._apply_search()
        # Selecciona primera coincidencia para "resaltar" visualmente
        self._refresh_listbox(select_first=True)

    def _on_return_keystroke(self, event=None) -> None:
        # Enter en el Entry -> confirmar la selección visible
        self._on_select_and_close()

    def _on_select_and_close(self, event=None) -> None:
        # Si no hay elementos visibles, no hacer nada
        if not self._visible:
            self.bell()
            return

        cur = self.listbox.curselection()
        if not cur:
            # Si no hay selección aún, tomar el primero
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
        self.result = None
        self.destroy()


def select_client(
    clients: List[Tuple[str, str]],
    parent: Optional[tk.Widget] = None,
    title: str = "Slect a client",
) -> Optional[str]:
    """
    Abre un popup modal para seleccionar un cliente.

    Parámetros
    ----------
    clients : List[Tuple[str, str]]
        Lista con formato: [('cliente1','id_cliente1'), ...]
    parent : tk.Widget | None
        Ventana padre (opcional). Si se pasa, el popup se centra sobre ella.
    title : str
        Título de la ventana.

    Retorna
    -------
    Optional[str]
        id_cliente del cliente seleccionado, o None si se cancela.
    """
    dlg = ClientSelectorDialog(parent=parent, clients=clients, title=title)
    return dlg.result