
from tkinter import ttk
import tkinter as tk

from ..components.utils import load_excel, error_window
from core import SCCD_CI_CONF, SCCD_SR



def main_function(root_win, sccd_user, sccd_pass, geo_callback=None):
    """
    Esta función muestra
    """
    geo_callback("420x180")
    sr = tk.StringVar()

    def create_conf_items():
        print("Please, select an Excel file (.xlsx) with configuration items data.")
        try:
            data = load_excel()
            if not data:
                return  # Si no se carga ningún archivo, salir de la función
            print("Creating configuration items...")
            sccd_connector = SCCD_CI_CONF(sccd_user, sccd_pass)
            result = sccd_connector.put_multiples_ci(data)

            # DEBUG: print type y contenido para entender qué está devolviendo la función
            print("DEBUG: put_multiples_ci result type:", type(result), "value:", repr(result))

            # Manejo seguro de la respuesta
            if isinstance(result, dict):
                if "success" in result:
                    print(result["success"])
                    return
                if "error" in result:
                    error_window(str(result["error"]))
                    return
                # Si es dict pero no tiene success/error, mostrarlo por si acaso
                error_window(str(result))
                return

            if isinstance(result, str):
                # Si la función devuelve una cadena "success" -> tratar como éxito
                if result.strip().lower().startswith("success"):
                    print(result)
                else:
                    error_window(result)
                return

            # Cualquier otro tipo inesperado
            error_window(str(result))

        except Exception as e:
            print("Exception error")
            error_window(f"Error: {e}")

    def assign_assets_button_function(sr):
        print("Please, select an Excel file (.xlsx) with assets to assign to the SR.")
        try:
            if not sr:
                error_window("Please, enter a valid SR number.")
                return
            print("Assigning assets to SR...")
            data = load_excel()    
            if not data:
                return  # If no file is loaded, exit the function
            sccd_connector = SCCD_SR(sccd_user, sccd_pass)
            sccd_connector.add_cis_to_sr(sr, data)
            print("All configuration items assigned to SR.")
        except Exception as e:
            error_window(f"Error: {e}")


    ttk.Button(root_win, text='Configuration Items Creator', command=lambda: create_conf_items()).pack(padx=15,pady=15) #Buttom to create configuration items from excel file .xlsx
    ttk.Label(root_win, text="SR: ").pack(side = 'left', padx=5, pady=15)
    ttk.Entry(root_win, textvariable=sr).pack(side = 'left', padx=5,pady=15) # SR Entry
    ttk.Button(root_win, text='Multi-Asset Assignment', command=lambda: assign_assets_button_function(sr.get())).pack(side = 'left', padx=5,pady=15) #Buttom to add assets/conf items to SR
