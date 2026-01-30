"""
Multi-Asset Assignment UI Module.

This module provides a simple interface for assigning multiple Configuration
Items (CIs/assets) from an Excel file to a Work Order or Task in SCCD.
"""

from tkinter import ttk
import tkinter as tk

from ..components.utils import load_excel, error_window
from core import SCCD_WO as SCCD


def main_function(root_win, sccd_owner: str, sccd_user: str, sccd_pass: str) -> None:
    """
    Entry point for the Multi-Asset Assignment module.

    Displays a form with a Work Order/Task ID entry field and a button
    to load assets from an Excel file and assign them to the specified
    work order in SCCD.

    Args:
        root_win: Parent Tkinter widget where the UI will be rendered
        sccd_owner: SCCD work order owner username
        sccd_user: SCCD login username
        sccd_pass: SCCD login password
    """
    wo_tk = tk.StringVar()

    def assign_assets_button_function(wo_id: str = None) -> None:
        """
        Load assets from Excel and assign them to the specified work order.

        Args:
            wo_id: Work Order or Task ID to assign assets to
        """
        try:
            data = load_excel()
            if not data:
                return  # Exit if no file was loaded
            sccd_connector = SCCD(sccd_owner, sccd_user, sccd_pass)
            result = sccd_connector.add_cis_to_work_order(wo_id, data)
            if "success" in result:
                print(result["success"])
            else:
                error_window(result.get("error", "Unknown error occurred"))
        except Exception as e:
            error_window(f"Error: {e}")

    # Multi-asset assignment button and input field
    ttk.Label(root_win, text="Work Order/Task ID:").pack(padx=15, pady=15)
    ttk.Entry(root_win, textvariable=wo_tk).pack(padx=15, pady=15)
    ttk.Button(
        root_win,
        text='Multi-Asset Assignment',
        command=lambda: assign_assets_button_function(wo_tk.get())
    ).pack(padx=15, pady=15)
