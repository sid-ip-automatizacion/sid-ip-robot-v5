
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

def export_treeview_to_excel(tree: ttk.Treeview):
    """
    Exporta todo el contenido de un ttk.Treeview a Excel,
    """
    # 1) Encabezados de las columnas
    cols = list(tree["columns"])
    headers = [tree.heading(c)["text"] or c for c in cols]

    # 2) Datos
    rows = []
    for iid in tree.get_children(""):
        values = tree.item(iid, "values")
        rows.append(values)

    if not rows:
        messagebox.showwarning("Exportar a Excel", "El Treeview no tiene datos.")
        return

    # 3) DataFrame
    df = pd.DataFrame(rows, columns=headers)

    # 4) Guardar archivo
    filepath = filedialog.asksaveasfilename(
        title="Guardar como",
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx")],
        confirmoverwrite=True,
    )
    if not filepath:
        return

    try:
        df.to_excel(filepath, index=False)
        messagebox.showinfo("Exportar a Excel", f"Archivo guardado:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar el archivo.\n{e}")