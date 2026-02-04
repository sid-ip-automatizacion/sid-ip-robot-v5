"""
SCCD Manager Module.

This module provides the AppStates class which is the main SCCD Work Order
management interface. It integrates the work order table, timers, and provides
functionality for updating states, adding logs, and exporting data.
"""

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint

from .sccd_table import Table
from .wo_timers import WorkOrderTimers
from core import SCCD_WO

from .utils import export_treeview_to_excel, parse_minutes
from .mw_email_gen import generate_MW_email

from .data import log_options, log_options_spanish, default_mw_text_1, default_mw_text_2


# ------------------- App wiring -------------------

class AppStates(tk.Toplevel):
    """
    Main SCCD Work Order Management application.

    Integrates the work order Table view with WorkOrderTimers controller
    for countdown functionality. Provides popups for updating work order
    states and adding logs. Uses ThreadPoolExecutor for non-blocking
    server updates.

    Attributes:
        table (Table): Work order data table widget
        executor (ThreadPoolExecutor): Thread pool for async server calls
        timers (WorkOrderTimers): Timer controller for countdown management
        sccd (SCCD_WO): SCCD API client for server operations
        on_close: Callback function invoked when window closes
    """

    def __init__(self, owner: str, user_sccd: str, pass_sccd: str, on_close=None):
        """
        Initialize the SCCD Work Order Manager window.

        Args:
            owner: Work order owner/assignee username
            user_sccd: SCCD login username
            pass_sccd: SCCD login password
            on_close: Optional callback for window close event
        """
        super().__init__()
        self.title("SCCD Work Orders Manager")

        # Absolute path to icon.ico file
        self.icon_path = Path(__file__).resolve().parent.parent.parent / 'resources' / 'icon.ico'
        self.iconbitmap(self.icon_path)

        # Table setup, columns and headings
        # Columns values correspond to SCCD get_work_orders dict keys
        self.columns = ["wo_id", "dc","description", "state", "last_update", "cid_count", "project_info", "pm", "time_min"]
        self.headings = ["WO ID ▲/▼", "DC ▲/▼", "Description ▲/▼", "Estate ▲/▼", "Last Update ▲/▼", "CID # ▲/▼", "Project Info ▲/▼", "PM ▲/▼", "Time (min) ▲/▼"]

        self.table = Table(self, columns=self.columns, headings=self.headings, height=14, user_sccd=user_sccd, pass_sccd=pass_sccd)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        # Executor for async DB updates (server calls)
        self.executor = ThreadPoolExecutor(max_workers=6)

        # Timers controller (GUI-safe)
        self.timers = WorkOrderTimers(
            tk_root=self,
            table_adapter=self.table,
            on_expire=self._on_timer_expired
        )
        # Initialize SCCD connector
        self.sccd = SCCD_WO(owner, user_sccd, pass_sccd)

        # Load initial data
        self.reload_from_db()

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(toolbar, text="Update State", command=self.open_update_state_popup).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Add log", command=self.open_add_log_popup).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Export to Excel", command=self.export_to_excel).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Clear", command=self.handle_clear).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Soft Clear", command=self.handle_soft_clear).pack(side="left", padx=6)
        # Search functionality
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        search_entry.bind("<Return>", lambda event: self.search_and_highlight())
        search_entry.pack(side="right", padx=6)
        ttk.Button(toolbar, text="Search", command=self.search_and_highlight).pack(side="right", padx=6)

        # on_close callback
        self.on_close = on_close

        # Make sure window closes cleanly
        self.protocol("WM_DELETE_WINDOW", self._on_close)





    # ---------- Data & server ops ----------

    def reload_from_db(self):
        """Reload work orders from the SCCD server into the table."""
        rows = self.sccd.get_work_orders()
        self.table.load(rows)

    def async_update_state_in_server(self, wo_id: str, new_state: str):
        """Dispatch a server update to a background thread (non-blocking)."""
        self.executor.submit(self.sccd.update_work_order_state, wo_id, new_state)

    def async_update_log_in_server(self, wo_id: str, title: str, note: str):
        """Dispatch a log update to a background thread (non-blocking)."""
        self.executor.submit(self.sccd.update_work_order_log, wo_id, title, note)

    def _on_timer_expired(self, wo_id: str):
        """Called when a timer reaches 0 (in GUI thread via timers)."""
        # Visually already set to WORKPENDING by timers; just notify server async
        self.async_update_state_in_server(wo_id, "WORKPENDING")

    # ---------- Clear behavior ----------

    def handle_clear(self):
        """Reset the view based on DB and stop all timers.
        - Reload from DB
        - Set all time_min to 0
        - Force state to WORKPENDING for any INPRG rows (both in view and server async)
        """
        self.timers.cancel_all()

        rows = self.sccd.get_work_orders()
        for row in rows:
            row["time_min"] = 0
            if row.get("state") == "INPRG":
                row["state"] = "WORKPENDING"
                self.async_update_state_in_server(row.get("wo_id", ""), "WORKPENDING")
        self.table.load(rows)
    
    def handle_soft_clear(self):
        """Reset the view based on DB and stop all timers.
        - Reload from DB
        - Set all time_min to 0
        """
        self.timers.cancel_all()

        rows = self.sccd.get_work_orders()
        for row in rows:
            row["time_min"] = 0
        self.table.load(rows)

    # ---------- Search behavior ----------
    def search_and_highlight(self):
        """Search the table for the query and highlight matching rows."""
        query = self.search_var.get().strip().lower()
        if not query:
            self.reset_highlights()
            return

        # Reset previous highlights
        self.reset_highlights()
        # Check each cell in the row for a match
        for iid in self.table.tree.get_children():
            values = self.table.tree.item(iid, "values")
            # Check if any cell contains the query (case insensitive)
            if any(query in str(celda).lower() for celda in values):
                # Add selection and make the row visible
                self.table.tree.selection_add(iid)
                self.table.tree.see(iid)
                # Apply an tag to highlight the row
                self.table.tree.item(iid, tags=("found",))
        # Configure the 'found' tag with a distinct background (e.g., yellow)
        self.table.tree.tag_configure("found", background="#A1A15E")
    
    def reset_highlights(self):
        """Remove selection and restore zebra striping style."""
        self.table.tree.selection_remove(self.table.tree.selection())
        for index, iid in enumerate(self.table.tree.get_children("")):
            tag = self.table.tag_even if index % 2 == 0 else self.table.tag_odd
            self.table.tree.item(iid, tags=(tag,))

    # ---------- Update State popup ----------

    def open_update_state_popup(self):
        """Open the Update State popup for selected work orders."""
        selected_rows = self.table.get_selected_full()

        popup = tk.Toplevel(self)
        popup.title("Update State")
        popup.geometry("600x440")
        popup.transient(self)
        popup.iconbitmap(self.icon_path)
        popup.grab_set()

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill="both", expand=True)

        if not selected_rows:
            ttk.Label(frame, text="No rows selected.").pack(anchor="w")
        else:
            ttk.Label(frame, text=f"Selected rows: {len(selected_rows)}").pack(anchor="w")

            cols = ("wo_id", "description", "state")
            preview = ttk.Treeview(frame, columns=cols, show="headings", height=8)
            for c in cols:
                preview.heading(c, text=c.upper())
                preview.column(c, width=180 if c != "state" else 120, anchor="w")
            preview.pack(fill="both", expand=True, pady=(8, 8))

            for r in selected_rows:
                preview.insert("", "end", values=(r.get("wo_id", ""), r.get("description", ""), r.get("state", "")))

            # State chooser
            form = ttk.Frame(frame)
            form.pack(fill="x", pady=(6, 0))

            ttk.Label(form, text="New state: ").grid(row=0, column=0, sticky="w")
            state_var = tk.StringVar(value="WORKPENDING")
            state_combo = ttk.Combobox(form, textvariable=state_var, values=["WORKPENDING", "INPRG"], state="readonly", width=16)
            state_combo.grid(row=0, column=1, sticky="w")

            # Timer minutes (INPRG only; 0 = no timer)
            ttk.Label(form, text="Time format 'mm' or 'hh:mm' (INPRG, 0 = no timer): ").grid(row=1, column=0, sticky="w", pady=(6,0))
            minutes_var = tk.StringVar(value="0")
            minutes_spin = ttk.Spinbox(form, from_=0, to=1440, textvariable=minutes_var, width=10, state="disabled")
            minutes_spin.grid(row=1, column=1, sticky="w", pady=(6,0))

            def on_state_change(*_):
                if state_var.get() == "INPRG":
                    minutes_spin.configure(state="normal")
                else:
                    minutes_spin.configure(state="disabled")
            state_combo.bind("<<ComboboxSelected>>", on_state_change)
            on_state_change()

            # Buttons
            btnbar = ttk.Frame(frame)
            btnbar.pack(fill="x", pady=(12, 0))

            def apply_changes():
                """Apply the selected state (and timer if INPRG) to all selected rows."""
                target_state = state_var.get()
                minutes = 0
                if target_state == "INPRG":
                    try:
                        minutes = parse_minutes(minutes_var.get()) # Use utility to parse and validate format (mm or hh:mm)
                        if minutes < 0:
                            raise ValueError
                    except Exception:
                        messagebox.showerror("Invalid minutes", "Please enter a non-negative integer for minutes.")
                        return

                # Apply locally and dispatch async server updates.
                for r in selected_rows:
                    wo_id = r.get("wo_id", "")
                    if not wo_id or not self.table.has_row(wo_id):
                        continue
                    self.table.set_state(wo_id, target_state)

                    if target_state == "INPRG":
                        if minutes > 0:
                            self.table.set_cell(wo_id, "time_min", str(minutes))
                            self.timers.start(wo_id, minutes)
                        else:
                            # INPRG without timer
                            self.timers.cancel(wo_id)
                            self.table.set_cell(wo_id, "time_min", "0")
                    else:
                        self.timers.cancel(wo_id)
                        self.table.set_cell(wo_id, "time_min", "0")

                    # Fire-and-forget server update
                    self.async_update_state_in_server(wo_id, target_state)

                popup.destroy()

            ttk.Button(btnbar, text="Apply", command=apply_changes).pack(side="left")
            ttk.Button(btnbar, text="Close", command=popup.destroy).pack(side="right")

    # ---------- Add log popup ----------

    def open_add_log_popup(self):
        """Open the Add Log popup for selected work orders."""
        selected_rows = self.table.get_selected_full()

        popup = tk.Toplevel(self)
        popup.title("Add log")
        popup.geometry("700x650")
        popup.transient(self)
        popup.iconbitmap(self.icon_path)
        popup.grab_set()

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill="both", expand=True)

        if not selected_rows:
            ttk.Label(frame, text="No rows selected.").pack(anchor="w")
        else:
            ttk.Label(frame, text=f"Selected rows: {len(selected_rows)}").pack(anchor="w")

            cols = ("wo_id", "description", "state")
            preview = ttk.Treeview(frame, columns=cols, show="headings", height=8)
            for c in cols:
                preview.heading(c, text=c.upper())
                preview.column(c, width=180 if c != "state" else 120, anchor="w")
            preview.pack(fill="both", expand=True, pady=(8, 8))

            for r in selected_rows:
                preview.insert("", "end", values=(r.get("wo_id", ""), r.get("description", ""), r.get("state", "")))

            form = ttk.Frame(frame)
            form.pack(fill="x", pady=(10, 0))

            # log options functions

            def select_log(event):
                title_entry.delete("1.0", "end") # Clear current text
                title_entry.insert("1.0", title_var.get()) # Insert selected log option
                note_text.delete("1.0", "end") # Clear note field
                note_text.insert("1.0", "Please add additional details here...") # default text
                if "N20." in title_var.get():
                    note_text.delete("1.0", "end")
                    note_text.insert("1.0", default_mw_text_1)
                elif "N21." in title_var.get():
                    note_text.delete("1.0", "end")
                    note_text.insert("1.0", default_mw_text_2)

            # Log title (from predefined options) + note

            # row 0
            ttk.Label(form, text="Title:").grid(row=0, column=0, sticky="w")
            title_var = tk.StringVar(value="")
            title_options = ttk.Combobox(form, textvariable=title_var, values=log_options, state="readonly", width=60)
            title_options.grid(row=0, column=1, sticky="w")
            title_options.bind("<<ComboboxSelected>>", select_log) # Bind selection event
            set_spanish = tk.BooleanVar(value=False)
            set_spanish_check = ttk.Checkbutton(form, text="Use Spanish log options", variable=set_spanish, command=lambda: title_options.configure(values=log_options_spanish if set_spanish.get() else log_options)) 
            set_spanish_check.grid(row=0, column=2, sticky="w")
            # row 1
            title_entry = tk.Text(form, width=50, height=1, wrap="word")
            title_entry.grid(row=1, column=1, sticky="w")
            ttk.Label(form, text="P00: Project Info; N27: PM Name").grid(row=1, column=2, sticky="e")
            # row 2
            ttk.Label(form, text="Note:").grid(row=2, column=0, sticky="nw", pady=(6,0))
            note_text = tk.Text(form, width=50, height=12, wrap="word")
            note_text.grid(row=2, column=1, sticky="w", pady=(6,0))

            btnbar = ttk.Frame(frame)
            btnbar.pack(fill="x", pady=(12, 0))
            

            def apply_log():
                """Apply the log entry to all selected rows."""
                title = title_entry.get("1.0", "end-1c")
                note = note_text.get("1.0", "end-1c").strip()

                if not title and not note:
                    messagebox.showerror("Empty log", "Please provide a title or a note.")
                    return

                # Optimistic UI update: apply to table immediately
                for r in selected_rows:
                    wo_id = r.get("wo_id", "")
                    if not wo_id or not self.table.has_row(wo_id):
                        continue

                    # Async server update
                    self.async_update_log_in_server(wo_id, title, note)
                    # Update last_update column visually
                    self.table.set_last_update(wo_id, note)
                    # If P00. is in title, update project_info column too
                    if 'P00.' in title:
                        self.table.set_project_info(wo_id, note)
                    # If N27. is in title, update pm column too
                    if 'N27.' in title:
                        self.table.set_pm(wo_id, note)
                        
                if 'N20.' in title or 'N21.' in title:
                    generate_MW_email(note)
                popup.destroy()

                 
            ttk.Button(btnbar, text="Apply", command=apply_log).pack(side="left")
            ttk.Button(btnbar, text="Close", command=popup.destroy).pack(side="right")

    # ---------- Export to Excel ----------
    def export_to_excel(self):
        export_treeview_to_excel(self.table.tree)

    # ---------- housekeeping ----------

    def _on_close(self):
        if callable(self.on_close):
            try:
                self.on_close()
            except Exception:
                pass
        try:
            self.timers.cancel_all()
        except Exception:
            pass
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self.destroy()

def run_sccd_manager(owner: str, user_sccd: str, pass_sccd: str, on_close=None) -> None:
    """
    Entry point for the SCCD Manager module.

    Creates and runs the SCCD Work Order Manager window.

    Args:
        owner: Work order owner/assignee username
        user_sccd: SCCD login username
        pass_sccd: SCCD login password
        on_close: Optional callback for window close event
    """
    app = AppStates(owner, user_sccd, pass_sccd, on_close=on_close)
    app.mainloop()


def main():
    """Standalone entry point for testing the SCCD Manager."""
    owner = " "  # Work order owner
    user_sccd = " "  # SCCD username
    pass_sccd = " "  # SCCD password
    app = AppStates(owner, user_sccd, pass_sccd)
    app.mainloop()


if __name__ == "__main__":
    main()