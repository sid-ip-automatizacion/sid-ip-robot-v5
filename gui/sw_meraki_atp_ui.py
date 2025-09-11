
import tkinter
from tkinter import ttk

from .components import error_window, save_excel, select_client
from core.meraki import get_switches, get_org


def get_atp_button_function(meraki_key_api):
    """
    Esta función obtiene la información de ATP de los switches Meraki y la guarda en un archivo Excel.
    """
    try:
        clients = get_org(meraki_key_api) #Se obtiene listado de las organizaciones
        org_id = select_client(clients) # Se selecciona la organización y se guarda el id
        info = get_switches(meraki_key_api, org_id) # Se obtiene la información de los switches Meraki
        save_excel(info) # Se guarda la información en un archivo Excel
        print("File saved")
    except Exception as e:
        error_window(f"Error: {e}")

def main_function(root_win, meraki_key_api):

    # Esta función mostrará el botón y  lo asociará a la función get_atp_button_function    
    # Botón para obtener ATP de los SWs
    btn_funcion1 = ttk.Button(root_win, text='Get ATP SW Meraki', command= lambda: get_atp_button_function(meraki_key_api))
    btn_funcion1.pack(pady=20)