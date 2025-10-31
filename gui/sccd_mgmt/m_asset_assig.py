
from tkinter import ttk
import tkinter as tk

from ..components.utils import load_excel, error_window
from core.sccd.sccd_connector import SCCD


def main_function(root_win, sccd_owner, sccd_user, sccd_pass):
    """
    Esta función muestra el botón para la asignación masiva de activos en SCCD y lo asocia al elemento correspondiente.
    Al hacer clic en el botón, se carga un archivo Excel con los datos de los activos.
    """
    wo_tk = tk.StringVar()

    def assign_assets_button_function(wo_id=None):
        try:
            data = load_excel()
            if not data:
                return  # Si no se carga ningún archivo, salir de la función
            sccd_connector = SCCD(sccd_owner, sccd_user, sccd_pass)
            result = sccd_connector.add_cis_to_work_order(wo_id, data)
            if "success" in result:
                print(result["success"])
            else:
                error_window(result.get("error", "Unknown error occurred"))
        except Exception as e:
            error_window(f"Error: {e}")

    # Botón para asignación masiva de activos en SCCD

    ttk.Label(root_win, text="Work Order/Task ID:").pack()
    ttk.Entry(root_win, textvariable=wo_tk).pack()
    ttk.Button(root_win, text='Multi-Asset Assignment', command=lambda: assign_assets_button_function(wo_tk.get())).pack()
