"""
Back Office Management UI Module.

This module provides a simple interface for back office operations including
creating Configuration Items (CIs) in SCCD from Excel files and assigning
assets to Service Requests (SRs).
"""

from tkinter import ttk
import tkinter as tk

from ..components.utils import load_excel, error_window
from core import SCCD_CI_CONF, SCCD_SR


def main_function(root_win, sccd_user: str, sccd_pass: str, geo_callback=None) -> None:
    """
    Entry point for the Back Office Management module.

    Displays buttons for creating Configuration Items and assigning assets
    to Service Requests in SCCD.

    Args:
        root_win: Parent Tkinter widget where the UI will be rendered
        sccd_user: SCCD login username
        sccd_pass: SCCD login password
        geo_callback: Optional callback to resize the main window
    """
    geo_callback("420x180")
    sr = tk.StringVar()

    def create_conf_items() -> None:
        """
        Create Configuration Items in SCCD from an Excel file.

        Prompts user to select an Excel file and creates CIs using the
        SCCD_CI_CONF connector.
        """
        print("Please, select an Excel file (.xlsx) with configuration items data.")
        try:
            data = load_excel()
            if not data:
                return  # Exit if no file was loaded
            print("Creating configuration items...")
            sccd_connector = SCCD_CI_CONF(sccd_user, sccd_pass)
            result = sccd_connector.put_multiples_ci(data)

            # DEBUG: print type and content to understand what the function returns
            print("DEBUG: put_multiples_ci result type:", type(result), "value:", repr(result))

            # Safe response handling
            if isinstance(result, dict):
                if "success" in result:
                    print(result["success"])
                    return
                if "error" in result:
                    error_window(str(result["error"]))
                    return
                # If dict but no success/error key, show it anyway
                error_window(str(result))
                return

            if isinstance(result, str):
                # If function returns a "success" string, treat as success
                if result.strip().lower().startswith("success"):
                    print(result)
                else:
                    error_window(result)
                return

            # Any other unexpected type
            error_window(str(result))

        except Exception as e:
            print("Exception error")
            error_window(f"Error: {e}")

    def assign_assets_button_function(sr_number: str) -> None:
        """
        Assign assets from an Excel file to a Service Request in SCCD.

        Args:
            sr_number: Service Request number to assign assets to
        """
        print("Please, select an Excel file (.xlsx) with assets to assign to the SR.")
        try:
            if not sr_number:
                error_window("Please, enter a valid SR number.")
                return
            print("Assigning assets to SR...")
            data = load_excel()
            if not data:
                return  # Exit if no file was loaded
            sccd_connector = SCCD_SR(sccd_user, sccd_pass)
            sccd_connector.add_cis_to_sr(sr_number, data)
            print("All configuration items assigned to SR.")
        except Exception as e:
            error_window(f"Error: {e}")

    # Button to create configuration items from Excel file
    ttk.Button(
        root_win,
        text='Configuration Items Creator',
        command=lambda: create_conf_items()
    ).pack(padx=15, pady=15)

    # Service Request entry and asset assignment button
    ttk.Label(root_win, text="SR: ").pack(side='left', padx=5, pady=15)
    ttk.Entry(root_win, textvariable=sr).pack(side='left', padx=5, pady=15)
    ttk.Button(
        root_win,
        text='Multi-Asset Assignment',
        command=lambda: assign_assets_button_function(sr.get())
    ).pack(side='left', padx=5, pady=15)
