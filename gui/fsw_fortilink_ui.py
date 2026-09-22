

import tkinter as tk
from tkinter import ttk


from core import FortigateSWController


def fsw_window(root_win) -> None:
    """
    Create a simple interface for retrieving FortiSwitch FortiLink information.

    Args:
        root_win: Parent Tkinter widget where the button will be placed
        fortinet_key_api: Fortinet API key for authentication
    """
    def get_fsw_button_function() -> None:
        """
        Retrieve FortiSwitch FortiLink information and print it to the console.
        """
        try:
            controller_ip = url.get()
            api_key_value = api_key.get()
            fortigate = FortigateSWController(controller_ip, api_key_value)
            switches = fortigate.get_switches()
            print(switches)
        except Exception as e:
            print(f"Error: {e}")

    
    url = tk.StringVar()
    ttk.Label(root_win, text="IP/URL").pack(side='left', padx=5, pady=15)
    ttk.Entry(root_win, textvariable=url).pack(side='left', padx=5, pady=15)

    api_key = tk.StringVar()
    ttk.Label(root_win, text="API Key").pack(side='left', padx=5, pady=15)
    ttk.Entry(root_win, textvariable=api_key, show="*").pack(side='left', padx=5, pady=15)


    # Button to retrieve FortiSwitch FortiLink information
    btn_fsw = ttk.Button(
        root_win,
        text='Document FSW in SCCD',
        command=lambda: get_fsw_button_function())
    btn_fsw.pack(side='left', padx=5, pady=15)

