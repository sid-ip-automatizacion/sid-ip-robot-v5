"""
SCCD Manager Utility Functions Module.

This module provides utility functions for the SCCD Manager interface,
including Excel export functionality and time parsing helpers.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd


def export_treeview_to_excel(tree: ttk.Treeview, callback=None) -> None:
    """
    Export all contents of a ttk.Treeview to an Excel file.

    Args:
        tree: The Treeview widget to export
        callback: Optional callback function to transform headers and rows
                 before export. Should accept (headers, rows) and return
                 (new_headers, new_rows).
    """
    # 1) Get column headers
    cols = list(tree["columns"])
    headers = [tree.heading(c)["text"].lower() or c for c in cols]

    # 2) Get row data
    rows = []
    for iid in tree.get_children(""):
        values = tree.item(iid, "values")
        rows.append(values)

    if not rows:
        messagebox.showwarning("Export to Excel", "The Treeview has no data.")
        return

    # 2.5) Optional callback to modify data before export
    new_headers = None
    new_rows = None
    if callback:
        new_headers, new_rows = callback(headers, rows)
    else:
        new_headers, new_rows = headers, rows

    # 3) Create DataFrame
    df = pd.DataFrame(new_rows, columns=new_headers)

    # 4) Save file dialog
    filepath = filedialog.asksaveasfilename(
        title="Save as",
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx")],
        confirmoverwrite=True,
    )
    print("File saved:", filepath)
    if not filepath:
        return

    try:
        df.to_excel(filepath, index=False)
        messagebox.showinfo("Export to Excel", f"File saved:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not export file.\n{e}")


def parse_minutes(entry: str) -> int:
    """
    Parse a time entry in 'hh:mm' format to minutes, or return minutes directly.

    Args:
        entry: Time string in 'hh:mm' format or plain minutes as string

    Returns:
        int: Total minutes

    Raises:
        ValueError: If the entry format is invalid
    """
    try:
        if ":" in entry:  # hh:mm format
            hh, mm = entry.split(":")
            total_minutes = int(hh) * 60 + int(mm)
            return total_minutes
        else:  # plain minutes
            return int(entry)
    except ValueError:
        raise ValueError(f"Invalid format: {entry}. Use 'hh:mm' or minutes as a number.")