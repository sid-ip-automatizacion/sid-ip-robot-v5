"""
GUI Utility Functions Module.

This module provides utility functions for the GUI including:
- Error dialog display
- Excel file save/load operations using pandas
"""

from pathlib import Path
import tkinter
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter.messagebox import showwarning

import pandas as pd

# Absolute path to azure.tcl theme file
theme_path = Path(__file__).resolve().parent.parent.parent / 'resources' / 'azure.tcl'


def error_window(text: str) -> None:
    """
    Display an error dialog window.

    Creates a simple Tkinter window showing an error message with an OK button.
    Uses the Azure dark theme for consistent styling.

    Args:
        text: Error message to display
    """
    print(f"ERROR: {text}")
    error_win = tkinter.Tk()
    error_win.tk.call("source", theme_path)
    error_win.tk.call("set_theme", "dark")
    error_text = tkinter.Label(error_win, text=text)
    ok_button = tkinter.Button(error_win, text='OK', width=5, height=2, command=error_win.destroy)
    error_text.pack()
    ok_button.pack()
    error_win.mainloop()


def infoW(title: str, info: str ) -> None:
    showwarning(title=title, message=info)



def save_excel(data: list) -> None:
    """
    Save data to an Excel file.

    Takes an array of dictionaries and generates an Excel file.
    Opens a save dialog for the user to choose the destination.

    Args:
        data: Array of dictionaries [{}, {}, {}...] to save as Excel
    """
    # Create DataFrame
    df = pd.DataFrame(data)

    # Open save file dialog
    file_path = asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="Save as"
    )

    if file_path:
        # Save DataFrame to Excel
        df.to_excel(file_path, index=False)
        print(f"File saved to: {file_path}")
    else:
        print("Save cancelled.")


def load_excel() -> list:
    """
    Load data from an Excel file.

    Opens a file dialog to select an Excel file and returns its contents
    as a list of dictionaries.

    The first row is interpreted as headers (keys).
    Keys are normalized to lowercase.

    Returns:
        list: List of dictionaries with data from the Excel file,
              or empty list if cancelled
    """
    file_path = askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        title="Open file"
    )

    if not file_path:
        print("Load cancelled.")
        return []

    df = pd.read_excel(file_path)
    # Normalize headers: convert to string, strip whitespace, lowercase
    df.columns = [str(c).strip().lower() for c in df.columns]

    return df.to_dict(orient="records")
