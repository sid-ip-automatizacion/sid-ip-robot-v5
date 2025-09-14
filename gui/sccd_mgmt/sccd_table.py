import tkinter as tk
from tkinter import ttk, messagebox
import json

from .utils import export_treeview_to_excel

class Table(ttk.Frame):
    """
    Enhanced ttk.Treeview table:
      - Columns & headings with sort indicators (▲/▼)
      - Double-click actions per column:
          * wo_id: copy to clipboard
          * description: copy to clipboard
          * last_update: popup with key/value table (copy on double-click)
          * cid_count: popup with CIDs table (copy on double-click)
      - Scrollbars (vertical/horizontal)
      - Zebra rows (even/odd)
      - Public API: load, clear_view, get_selected(), get_selected_full()
      - Helper API: set_cell(wo_id, col, value), set_state(wo_id, state), has_row(wo_id)
    """
    def __init__(self, parent, columns, headings=None, show='headings', height=12):
        super().__init__(parent)
        self.columns = columns
        self.headings = headings or columns

        # Store original rows keyed by iid (wo_id)
        self._row_store = {}

        # Base heading text map (strip placeholders like ▲/▼)
        self._base_headings = {}
        for col, head in zip(self.columns, self.headings):
            self._base_headings[col] = self._strip_arrows(head)

        # Table + scrollbars
        self.tree = ttk.Treeview(self, columns=self.columns, show=show, height=height)
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure columns and headings
        for col in self.columns:
            self.tree.heading(col, text=f"{self._base_headings[col]} ▲/▼",
                              command=lambda c=col: self._sort_by(c, False))
            anchor = "e" if col in ("time_min", "cid_count") else "w"
            width = 200 if col in ("description", "last_update", "project_info") else 110
            self.tree.column(col, width=width, anchor=anchor, stretch=True)

        # Zebra tags
        self.tag_even = "evenrow"
        self.tag_odd = "oddrow"
        self.tree.tag_configure(self.tag_even, background="#717794") # zebra
        self.tree.tag_configure(self.tag_odd, background="#525768") # zebra

        # Events
        self.tree.bind("<Double-1>", self._on_double_click)  # context-aware double click
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Sort state
        self._sort_state = {c: None for c in self.columns}

    # -------------------- Public API --------------------

    def load(self, rows):
        """Load data into the table from a list of dicts or sequences."""
        self.clear_view()
        is_dicts = len(rows) > 0 and isinstance(rows[0], dict)
        for i, row in enumerate(rows):
            if is_dicts:
                iid = row.get("wo_id", "")
                if not iid:
                    iid = self.tree.insert("", "end")  # temp
                    self.tree.delete(iid)

                # derive cid_count from 'cids' list
                cid_count = len(row.get("cids", []))
                # build values for visible columns
                vals = []
                for col in self.columns:
                    if col == "cid_count":
                        vals.append(str(cid_count))
                    else:
                        vals.append(self._format_cell(col, row.get(col, "")))

                tag = self.tag_even if i % 2 == 0 else self.tag_odd # zebra
                self.tree.insert("", "end", iid=iid, values=vals, tags=(tag,)) # zebra
                self._row_store[iid] = row.copy()
            else:
                tag = self.tag_even if i % 2 == 0 else self.tag_odd # zebra
                self.tree.insert("", "end", values=row, tags=(tag,)) # zebra


        # Reset sort indicators
        for col in self.columns:
            self._set_heading(col, arrow="▲/▼", next_desc=False)

    def clear_view(self):
        """Clear rows from the view (does not touch external DB)."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._row_store.clear()

    def get_selected(self):
        """Return a list of dicts {col: value} using displayed string values."""
        result = []
        for item in self.tree.selection():
            values = self.tree.item(item, "values")
            result.append({col: values[i] for i, col in enumerate(self.columns)})
        return result

    def get_selected_full(self):
        """Return original stored rows (dicts) for selected iids if available."""
        full = []
        for iid in self.tree.selection():
            if iid in self._row_store:
                full.append(self._row_store[iid].copy())
            else:
                values = self.tree.item(iid, "values")
                full.append({col: values[i] for i, col in enumerate(self.columns)})
        return full

    def set_cell(self, wo_id: str, column: str, value: str):
        """Set a single cell value in both view and row_store (if present)."""
        if not self.has_row(wo_id):
            return
        values = list(self.tree.item(wo_id, "values"))
        idx = self.columns.index(column)
        if len(values) < len(self.columns):
            values += [""] * (len(self.columns) - len(values))  # <-- fixed length calc
        values[idx] = str(value)
        self.tree.item(wo_id, values=values)

        if wo_id in self._row_store:
            # keep underlying store coherent
            self._row_store[wo_id][column] = value

    def set_state(self, wo_id: str, new_state: str):
        """Update the 'state' column in the table/row_store."""
        self.set_cell(wo_id, "state", new_state)

    def set_last_update(self, wo_id: str, last_update: str):
        """Update the 'last_update' column in the table/row_store."""
        self.set_cell(wo_id, "last_update", last_update)

    def set_project_info(self, wo_id: str, project_info: str):
        """Update the 'project_info' column in the table/row_store."""
        self.set_cell(wo_id, "project_info", project_info)

    def has_row(self, wo_id: str) -> bool:
        return bool(self.tree.exists(wo_id))

    # -------------------- Events & Sorting --------------------

    def _on_select(self, _event):
        pass  # hook point if needed

    def _on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)  # e.g., '#1'
        if not row_id or not col_id:
            return

        col_index = int(col_id.replace("#", "")) - 1
        column = self.columns[col_index]
        # Get underlying value (prefer original store)
        row = self._row_store.get(row_id)
        display_values = self.tree.item(row_id, "values")
        cell_value = (row.get(column) if row and column in row else display_values[col_index])

        # Column-specific behaviors
        if column == "wo_id":
            self._copy_to_clipboard(str(cell_value))
            return
        if column == "description":
            self._copy_to_clipboard(str(cell_value))
            return
        if column == "last_update" or column == "project_info":
            self._open_info_popup(row_id, row, col_id)
            return
        if column == "cid_count":
            self._open_cids_table_popup(row_id, row)
            return

    def _sort_by(self, col, descending):
        data = []
        for iid in self.tree.get_children(""):
            val = self.tree.set(iid, col)
            key = self._coerce_for_sort(col, val, iid)
            data.append((key, iid))

        data.sort(reverse=descending, key=lambda x: (self._is_none(x[0]), x[0]))

        for index, (_, iid) in enumerate(data):
            self.tree.move(iid, "", index)
        
        # Aplicar el estilo zebra según la nueva posición
        for index, iid in enumerate(self.tree.get_children("")):
            tag = self.tag_even if index % 2 == 0 else self.tag_odd
            self.tree.item(iid, tags=(tag,))

        self._sort_state[col] = descending
        self._set_sort_indicators(active_col=col, descending=descending)

    def _set_sort_indicators(self, active_col, descending):
        for col in self.columns:
            if col == active_col:
                arrow = "▼" if descending else "▲"
                next_desc = not descending
            else:
                arrow = "▲/▼"
                next_desc = False
            self._set_heading(col, arrow=arrow, next_desc=next_desc)

    def _set_heading(self, col, arrow="▲/▼", next_desc=False):
        base = self._base_headings[col]
        self.tree.heading(col,
                          text=f"{base} {arrow}",
                          command=lambda c=col, d=next_desc: self._sort_by(c, d))

    # -------------------- Popups --------------------

    def _open_info_popup(self, iid, row, col_id):
        popup = tk.Toplevel(self)
        if col_id == "#4":
            popup.title(f"Information - {iid}")
            payload = (row or {}).get("last_update", "no info") if row else " no info"
            if row and "last_update" in row:
                payload = row["last_update"]
        if col_id == "#6":
            popup.title(f"Project Info - {iid}")
            payload = (row or {}).get("project_info", "no info") if row else " no info"
            if row and "project_info" in row:
                payload = row["project_info"]

        popup.geometry("560x360")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        container = ttk.Frame(popup, padding=10)
        container.pack(fill="both", expand=True)

        text = tk.Text(container, wrap="word", height=14)
        text.pack(fill="both", expand=True)
        try:
            if isinstance(payload, (dict, list)):
                rendered = json.dumps(payload, indent=2, ensure_ascii=False)
            else:
                rendered = str(payload)
        except Exception:
            rendered = str(payload)

        text.insert("1.0", rendered)
        text.configure(state="disabled")

        btnbar = ttk.Frame(container)
        btnbar.pack(fill="x", pady=(8, 0))

        def copy_json():
            self._copy_to_clipboard(rendered)

        ttk.Button(btnbar, text="Copy", command=copy_json).pack(side="left")
        ttk.Button(btnbar, text="Close", command=popup.destroy).pack(side="right")




    def _open_cids_table_popup(self, iid, row):
        popup = tk.Toplevel(self)
        popup.title(f"CIDs - {iid}")
        popup.geometry("600x360")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        container = ttk.Frame(popup, padding=10)
        container.pack(fill="both", expand=True)

        columns = ("cid", "location", "description")
        tv = ttk.Treeview(container, columns=columns, show="headings", height=10)
        for c in columns:
            tv.heading(c, text=c.upper())
            w = 160 if c != "description" else 260
            tv.column(c, width=w, anchor="w", stretch=True)
        tv.pack(fill="both", expand=True)

        items = (row or {}).get("cids", []) if row else []
        for it in items:
            tv.insert("", "end", values=(it.get("cid", ""), it.get("location", ""), it.get("description", "")))

        def on_copy(event):
            region = tv.identify("region", event.x, event.y)
            if region != "cell":
                return
            item = tv.identify_row(event.y)
            col_id = tv.identify_column(event.x)
            if not item or not col_id:
                return
            idx = int(col_id.replace("#", "")) - 1
            vals = tv.item(item, "values")
            if 0 <= idx < len(vals):
                self._copy_to_clipboard(str(vals[idx]))

        tv.bind("<Double-1>", on_copy)

        btnbar = ttk.Frame(container)
        btnbar.pack(fill="x", pady=(8, 0))
        ttk.Button(btnbar, text="Export to Excel", command=lambda: export_treeview_to_excel(tv)).pack(side="left")
        ttk.Button(btnbar, text="Close", command=popup.destroy).pack(side="right")

    # -------------------- Helpers --------------------

    @staticmethod
    def _strip_arrows(text: str) -> str:
        return (text.replace("▲/▼", "").replace("▲", "").replace("▼", "")).strip()

    def _copy_to_clipboard(self, text: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            top = self.winfo_toplevel()
            original = top.title()
            top.title(f"Copied: {text}")
            top.after(900, lambda: top.title(original))
        except Exception:
            messagebox.showinfo("Copied", text)

    def _format_cell(self, col, value):
        if col == "last_update" or col == "project_info":
            if isinstance(value, dict):
                return value.get("title") or json.dumps(value, ensure_ascii=False)
            return str(value)
        if col in ("time_min", "cid_count"):
            return str(value)
        return str(value)

    @staticmethod
    def _is_none(v):
        return v is None

    def _coerce_for_sort(self, col, val, iid):
        if col == "last_update":
            row = self._row_store.get(iid)
            if row:
                lu = row.get("last_update")
                if isinstance(lu, dict):
                    ts = lu.get("timestamp") or lu.get("time")
                    if ts:
                        dt = self._parse_datetime(ts)
                        if dt:
                            return dt
            dt = self._parse_datetime(val)
            if dt:
                return dt
        if col == "project_info":
            row = self._row_store.get(iid)
            if row:
                pi = row.get("project_info")
                if isinstance(pi, dict):
                    name = pi.get("name")
                    if name:
                        return name.lower()
            return str(val).lower()

        if val is None or val == "":
            return None
        try:
            if isinstance(val, str) and val.strip().isdigit():
                return int(val)
            return float(val)
        except Exception:
            pass

        dt = self._parse_datetime(val)
        if dt:
            return dt

        return str(val).lower()

    @staticmethod
    def _parse_datetime(s):
        if not isinstance(s, str):
            return None
        s = s.strip()
        fmts = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ]
        try:
            from datetime import datetime as _dt
            return _dt.fromisoformat(s)
        except Exception:
            pass
        from datetime import datetime as _dt
        for f in fmts:
            try:
                return _dt.strptime(s, f)
            except Exception:
                continue
        return None
