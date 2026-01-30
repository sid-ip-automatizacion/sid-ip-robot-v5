"""
AP SCCD Documentation UI Module.

This module provides the AP_SCCD_Doc_UI class for capturing SCCD (Service Desk)
documentation parameters when configuring Access Points. It provides an expandable
form for entering CI configuration details like controller CID, VLAN, and deal code.
"""

import tkinter as tk
from tkinter import ttk


class AP_SCCD_Doc_UI:
    """
    SCCD Documentation UI Component for Access Point Configuration.

    Provides an expandable checkbox-activated form for entering SCCD CI
    configuration parameters when updating Access Points on controllers.

    Attributes:
        parent: Parent Tkinter widget
        sccd_doc (BooleanVar): Whether SCCD documentation is enabled
        owner_by_customer (BooleanVar): Whether the device is owned by customer
        managed_by_customer (BooleanVar): Whether the device is managed by customer
        controller_cid (StringVar): Controller Configuration Item ID
        control_vlan (StringVar): Control VLAN for the APs
        dealcode (StringVar): Deal/project code
        sup_info (StringVar): Support expiration information
        geo_callback: Callback function to resize the main window
    """

    def __init__(self, parent, geo_callback=None):
        """
        Initialize the AP SCCD Documentation UI.

        Args:
            parent: Parent Tkinter widget where the UI will be rendered
            geo_callback: Optional callback to resize the main window when
                         the SCCD fields are shown/hidden
        """
        self.parent = parent
        self.sccd_doc = tk.BooleanVar(value=False)
        self.owner_by_customer = tk.BooleanVar(value=False)
        self.managed_by_customer = tk.BooleanVar(value=False)
        self.controller_cid = tk.StringVar(value="")
        self.control_vlan = tk.StringVar(value="")
        self.dealcode = tk.StringVar(value="")
        self.sup_info = tk.StringVar(value="")

        self.sccd_doc_frame = ttk.Frame(self.parent)
        self.sccd_doc_check = ttk.Checkbutton(
            self.sccd_doc_frame,
            text="Enable SCCD Documentation (Only for AP Configuration)",
            variable=self.sccd_doc,
            command=self.toggle_sccd_variables
        )
        self.sccd_varibles_frame = ttk.Frame(self.sccd_doc_frame)
        self.sccd_doc_frame.pack(pady=10)
        self.sccd_doc_check.pack(pady=5)
        self.sccd_varibles_frame.pack(pady=5)

        self.geo_callback = geo_callback

    def toggle_sccd_variables(self) -> None:
        """Toggle visibility of SCCD variable input fields based on checkbox state."""
        if self.sccd_doc.get():
            # Show SCCD variable inputs and resize window
            self.geo_callback("700x550")
            self.show_sccd_variable_inputs()
        else:
            # Hide SCCD variable inputs
            self.hide_sccd_variable_inputs()

    def show_sccd_variable_inputs(self) -> None:
        """Display the SCCD variable input fields in the form."""
        # Ownership and management checkboxes
        ttk.Checkbutton(
            self.sccd_varibles_frame,
            text="Owner by Customer",
            variable=self.owner_by_customer
        ).grid(row=0, column=1)

        ttk.Checkbutton(
            self.sccd_varibles_frame,
            text="Managed by Customer",
            variable=self.managed_by_customer
        ).grid(row=0, column=2)

        # Controller CID field
        ttk.Label(self.sccd_varibles_frame, text="Controller CID:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.controller_cid).grid(row=1, column=1)

        # Control VLAN field
        ttk.Label(self.sccd_varibles_frame, text="Control VLAN:").grid(row=1, column=2, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.control_vlan).grid(row=1, column=3)

        # Deal code field
        ttk.Label(self.sccd_varibles_frame, text="Deal Code:").grid(row=2, column=0, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.dealcode).grid(row=2, column=1)

        # Support information field
        ttk.Label(self.sccd_varibles_frame, text="Support Information:").grid(row=2, column=2, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.sup_info).grid(row=2, column=3)

    def hide_sccd_variable_inputs(self) -> None:
        """Hide all SCCD variable input fields from the form."""
        for widget in self.sccd_varibles_frame.winfo_children():
            widget.grid_forget()