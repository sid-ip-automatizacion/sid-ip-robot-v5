
import tkinter as tk
from tkinter import ttk


class AP_SCCD_Doc_UI:
    def __init__(self, parent, geo_callback=None):
        self.parent = parent
        self.sccd_doc = tk.BooleanVar(value=False)
        self.owner_by_customer = tk.BooleanVar(value=False)
        self.managed_by_customer = tk.BooleanVar(value=False)
        self.controller_cidr = tk.StringVar(value="")
        self.control_vlan = tk.StringVar(value="")
        self.dealcode = tk.StringVar(value="")
        self.sup_info = tk.StringVar(value="")

        self.sccd_doc_frame = ttk.Frame(self.parent)
        self.sccd_doc_check = ttk.Checkbutton(self.sccd_doc_frame, text="Enable SCCD Documentation (Only for AP Configuration)", variable=self.sccd_doc, command=self.toggle_sccd_variables)
        self.sccd_varibles_frame = ttk.Frame(self.sccd_doc_frame)
        self.sccd_doc_frame.pack(pady=10)
        self.sccd_doc_check.pack(pady=5)
        self.sccd_varibles_frame.pack(pady=5)

        self.geo_callback = geo_callback
        
        

    def toggle_sccd_variables(self):
        if self.sccd_doc.get():
            # Show SCCD variable inputs
            self.geo_callback("700x550")
            self.show_sccd_variable_inputs()
        else:
            # Hide SCCD variable inputs
            self.hide_sccd_variable_inputs()

    def show_sccd_variable_inputs(self):
        # Show the SCCD variable input fields
        ttk.Checkbutton(self.sccd_varibles_frame, text="Owner by Customer", variable=self.owner_by_customer).grid(row=0, column=1)

        ttk.Checkbutton(self.sccd_varibles_frame, text="Managed by Customer", variable=self.managed_by_customer).grid(row=0, column=2)

        ttk.Label(self.sccd_varibles_frame, text="Controller CID:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.controller_cidr).grid(row=1, column=1)

        ttk.Label(self.sccd_varibles_frame, text="Control VLAN:").grid(row=1, column=2, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.control_vlan).grid(row=1, column=3)

        ttk.Label(self.sccd_varibles_frame, text="Deal Code:").grid(row=2, column=0, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.dealcode).grid(row=2, column=1)

        ttk.Label(self.sccd_varibles_frame, text="Support Information:").grid(row=2, column=2, sticky="w")
        ttk.Entry(self.sccd_varibles_frame, textvariable=self.sup_info).grid(row=2, column=3)

    def hide_sccd_variable_inputs(self):
        # Hide the SCCD variable input fields
        for widget in self.sccd_varibles_frame.winfo_children():
            widget.grid_forget()