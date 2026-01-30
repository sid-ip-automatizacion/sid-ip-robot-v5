"""
Meraki Switch ATP UI Module.

This module provides a simple interface for retrieving ATP (Access Point)
information from Meraki switches and exporting it to an Excel file.
"""

import tkinter
from tkinter import ttk

from .components import error_window, save_excel, select_client
from core.meraki import get_switches, get_org


def get_atp_button_function(meraki_key_api: str) -> None:
    """
    Retrieve ATP information from Meraki switches and save to Excel.

    Prompts the user to select an organization, retrieves switch information,
    and saves the data to an Excel file.

    Args:
        meraki_key_api: Meraki API key for authentication
    """
    try:
        clients = get_org(meraki_key_api)  # Get list of organizations
        org_id = select_client(clients)  # Select organization and get its ID
        info = get_switches(meraki_key_api, org_id)  # Get Meraki switch information
        save_excel(info)  # Save information to Excel file
        print("File saved")
    except Exception as e:
        error_window(f"Error: {e}")


def main_function(root_win, meraki_key_api: str) -> None:
    """
    Entry point for the Meraki Switch ATP module.

    Creates a button in the provided window that triggers ATP data retrieval.

    Args:
        root_win: Parent Tkinter widget where the button will be placed
        meraki_key_api: Meraki API key for authentication
    """
    # Button to retrieve ATP information from switches
    btn_funcion1 = ttk.Button(
        root_win,
        text='Get ATP SW Meraki',
        command=lambda: get_atp_button_function(meraki_key_api)
    )
    btn_funcion1.pack(pady=20)