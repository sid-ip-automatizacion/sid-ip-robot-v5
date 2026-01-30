"""
AP Management UI Module.

This module provides the APManagementGUI class for managing Access Points
from different vendors (Ruckus, Meraki, Fortinet) through a graphical interface.
It supports retrieving AP information and updating AP configurations on controllers.
"""

from pathlib import Path


import tkinter
from tkinter import ttk

from core.ap_management import get_controller
from core.ruckus import get_domains
from core.meraki import get_org
from core import SCCD_CI_CONF

from gui.ap_sccd_doc_ui import AP_SCCD_Doc_UI
from .components import error_window, save_excel, select_client, load_excel


class APManagementGUI:
    """
    Access Point Management GUI.

    Provides a graphical interface for managing Access Points from multiple
    vendors including Ruckus SmartZone, Meraki, and Fortinet controllers.
    Supports retrieving AP lists and updating AP configurations.

    Attributes:
        master: Parent Tkinter widget
        current_state (StringVar): Current operation status message
        vendor_selected (str): Selected vendor ('ruckus', 'meraki', 'forti')
        controller_info (dict): Controller connection and configuration data
        geo_callback: Callback function to resize the main window
        ap_sccd_doc_ui (AP_SCCD_Doc_UI): SCCD documentation UI component
    """

    def __init__(self, root_window, meraki_api_key, sccd_username, sccd_pass, geo_callback=None):
        """
        Initialize the AP Management GUI.

        Args:
            root_window: Parent Tkinter widget where UI will be rendered
            meraki_api_key: Meraki API key for authentication
            sccd_username: SCCD username for CI configuration
            sccd_pass: SCCD password for CI configuration
            geo_callback: Optional callback to resize the main window
        """
        self.master = root_window
        self.current_state = tkinter.StringVar()
        self.current_state.set("select vendor and fill data")
        self.vendor_selected = None
        self.login_user = tkinter.StringVar()
        self.login_pass = tkinter.StringVar()
        self.url = tkinter.StringVar()
        self.fortikey = tkinter.StringVar()

        self.geo_callback = geo_callback
        self.geo_callback("400x400")
        self.ap_sccd_doc_ui = None
        self.sccd_username = sccd_username
        self.sccd_pass = sccd_pass

        self.controller_info = {
            "vendor": None,
            "login_user": None,
            "login_password": None,
            "login_url": None,
            "ruckus_domain_id": None,
            "meraki_api_key": meraki_api_key,
            "meraki_org_id": None,
            "forti_key": None,
            "ap_list": None
            }

    def clear_work_area(self):
        """Clear all widgets from the work area."""
        for widget in self.master.winfo_children():
            widget.destroy()

    def set_controller_info(self):
        """
        Set the controller information from form inputs.

        Updates the controller_info dictionary with the current form values
        and handles vendor-specific setup (domain selection for Ruckus,
        organization selection for Meraki, API key for Fortinet).
        """
        self.current_state.set("working...")
        self.controller_info['vendor'] = self.vendor_selected
        self.controller_info['login_user'] = self.login_user.get()
        self.controller_info['login_password'] = self.login_pass.get()
        self.controller_info['login_url'] = self.url.get()
        self.controller_info['forti_key'] = self.fortikey.get()

        print(self.controller_info)
        if self.vendor_selected == 'ruckus':
            if not self.controller_info['login_user'] or not self.controller_info['login_password']:
                error_window("Login user and password are required for Ruckus.")
                return
            if not self.controller_info['login_url']:
                error_window("Login URL is required for Ruckus.")
                return
            self.current_state.set("selecting domain...")
            domains = get_domains(
                self.controller_info['login_url'],
                self.controller_info['login_user'],
                self.controller_info['login_password']
            )
            if domains:
                self.controller_info['ruckus_domain_id'] = select_client(domains)
                print("Selected domain:", self.controller_info['ruckus_domain_id'])
            else:
                self.controller_info['ruckus_domain_id'] = '0'
        elif self.vendor_selected == 'meraki':
            orgs = get_org(self.controller_info['meraki_api_key'])
            if orgs:
                self.current_state.set("selecting organization...")
                self.controller_info['meraki_org_id'] = select_client(orgs)
                print("Selected organization:", self.controller_info['meraki_org_id'])
            else:
                error_window("No organizations found for the provided API key.")
                return
        elif self.vendor_selected == 'forti':
            if not self.controller_info['forti_key']:
                error_window("Fortigate API key is required.")
                return
            if not self.controller_info['login_url']:
                error_window("Fortigate URL is required.")
                return
            self.controller_info['forti_key'] = self.fortikey.get()
            self.controller_info['login_url'] = self.url.get()

        print("Controller info set:", self.controller_info)


    def get(self):
        """
        Retrieve AP information and save to Excel file.

        Gets the list of Access Points from the configured controller
        and prompts the user to save the data to an Excel file.
        """
        try:
            self.set_controller_info()  # Set controller information from form
            controller = get_controller(self.controller_info)  # Create controller based on controller_info
            apinfo = controller.get()  # Retrieve AP information from controller
            self.current_state.set("please save the file")
            save_excel(apinfo)  # Save AP information to Excel file
            self.current_state.set("file saved")
            print("File saved")
        except Exception as e:
            error_window(f"Error retrieving AP information: {e}")
            print(f"Error retrieving AP information: {e}")
            
    def put(self):
        """
        Update AP name, description, and address information on the controller.

        Loads AP configuration from an Excel file and pushes the updates
        to the wireless controller. If SCCD documentation is enabled,
        also updates the Configuration Items (CIs) in SCCD.
        """

        try:
            self.set_controller_info()  # Set controller information from form
            self.controller_info['ap_list'] = load_excel()  # Load AP list from Excel file
            controller = get_controller(self.controller_info)  # Create controller based on controller_info
            controller.put()  # Send AP information to the controller
            self.current_state.set("AP information updated successfully")
            print("AP information updated successfully on the controller")

            if self.ap_sccd_doc_ui.sccd_doc.get():  # If SCCD documentation is enabled, update SCCD
                # Vendor normalization for SCCD
                vendor = None
                if self.vendor_selected == 'ruckus':
                    vendor = 'Ruckus'
                elif self.vendor_selected == 'meraki':
                    vendor = 'Meraki'
                elif self.vendor_selected == 'forti':
                    vendor = 'Fortinet'
                try:
                    # SCCD CI Configuration
                    sccd_ap_ci_config = SCCD_CI_CONF(self.sccd_username, self.sccd_pass)
                    sccd_ap_ci_config.update_multiple_aps_ci(
                        self.controller_info['ap_list'],  # Update SCCD CI for multiple APs
                        vendor=vendor,  # Vendor name
                        controller=self.ap_sccd_doc_ui.controller_cid.get(),  # Controller CID
                        control_vlan=self.ap_sccd_doc_ui.control_vlan.get(),  # Control VLAN
                        dealcode=self.ap_sccd_doc_ui.dealcode.get(),  # Deal code
                        managed_by="Managed Level 2" if self.ap_sccd_doc_ui.managed_by_customer.get() else "CW",
                        owner_by="CUSTOMER" if self.ap_sccd_doc_ui.owner_by_customer.get() else "CW",
                        sup_exp=self.ap_sccd_doc_ui.sup_info.get()  # Support expiration date
                    )
                except Exception as e:
                    error_window(f"Error initializing SCCD CI Configurator: {e}")
                    print(f"Error initializing SCCD CI Configurator: {e}")
                    return

        except Exception as e:
            error_window(f"Error updating AP information: {e}")
            print(f"Error updating AP information: {e}")
            return


    def draw(self):
        """
        Draw the AP Management graphical interface.

        Creates the form with fields for selecting vendor, entering credentials,
        and controller URL. Includes buttons for retrieving AP information and
        configuring APs. Also displays a status message to inform the user
        about operation progress.
        """
        def select_vendor(event):
            """Handle vendor selection and enable/disable appropriate fields."""
            vendors_label_map = {'Ruckus-SZ': 'ruckus', 'Meraki': 'meraki', 'Fortinet': 'forti'}
            self.vendor_selected = vendors_label_map[selected_vendor.get()]
            self.controller_info['vendor'] = self.vendor_selected
            if self.vendor_selected == 'meraki':
                user_ent.config(state='disabled')
                pass_ent.config(state='disabled')
                url_ent.config(state='disabled')
                fortikey_ent.config(state='disabled')
            elif self.vendor_selected == 'forti':
                user_ent.config(state='disabled')
                pass_ent.config(state='disabled')
                url_ent.config(state='normal')
                fortikey_ent.config(state='normal')
            else:
                user_ent.config(state='normal')
                pass_ent.config(state='normal')
                url_ent.config(state='normal')
                fortikey_ent.config(state='disabled')

        self.clear_work_area()  # Clear work area before drawing the interface
        self.frm = tkinter.Frame(self.master)
        self.frm.grid(row=0, column=0)
        self.frm.rowconfigure(0, weight=1, minsize=10)
        self.frm.rowconfigure(1, weight=1, minsize=10)
        self.frm.rowconfigure(2, weight=1, minsize=10)
        self.frm.rowconfigure(3, weight=1, minsize=10)
        self.frm.rowconfigure(4, weight=1, minsize=10)
        self.frm.rowconfigure(5, weight=1, minsize=10)
        self.frm.rowconfigure(6, weight=1, minsize=10)
        self.frm.rowconfigure(7, weight=1, minsize=10)
        self.frm.rowconfigure(8, weight=1, minsize=10)
        self.frm.rowconfigure(9, weight=1, minsize=10)
        self.frm.columnconfigure(0, weight=1, minsize=10)
        self.frm.columnconfigure(1, weight=1, minsize=10)

        # Title label
        title_lb = ttk.Label(self.frm, text="ACCESS POINTS MANAGER", anchor=tkinter.CENTER, font=('Helvetica', 12))
        title_lb.grid(row=0, columnspan=2, pady=10)

        # Vendor dropdown selector
        selected_vendor = tkinter.StringVar(self.frm)
        vendor_lb = ttk.Label(self.frm, text="Choose vendor")
        vendor_lb.grid(row=1, column=0, sticky=tkinter.E)
        cb_vendors = ttk.Combobox(self.frm, state='readonly', textvariable=selected_vendor)
        cb_vendors['values'] = ['Ruckus-SZ', 'Meraki', 'Fortinet']
        cb_vendors.grid(row=1, column=1, sticky=tkinter.W)
        cb_vendors.bind('<<ComboboxSelected>>', select_vendor)

        # Username entry field
        user_lb = ttk.Label(self.frm, text="Login user")
        user_lb.grid(row=2, column=0, sticky=tkinter.E)
        user_ent = ttk.Entry(self.frm, textvariable=self.login_user, width=20)
        user_ent.grid(row=2, column=1, sticky=tkinter.W)
        user_ent.config(state='disabled')

        # Password entry field
        pass_lb = ttk.Label(self.frm, text="Password")
        pass_lb.grid(row=3, column=0, sticky=tkinter.E)
        pass_ent = ttk.Entry(self.frm, show='*', textvariable=self.login_pass, width=20)
        pass_ent.grid(row=3, column=1, sticky=tkinter.W)
        pass_ent.config(state='disabled')

        # Controller URL entry field
        url_lb = ttk.Label(self.frm, text="Controller URL")
        url_lb.grid(row=4, column=0, sticky=tkinter.E)
        url_ent = ttk.Entry(self.frm, textvariable=self.url, width=20)
        url_ent.grid(row=4, column=1, sticky=tkinter.W)
        url_ent.config(state='disabled')

        # Fortigate API key entry field
        fortikey_lb = ttk.Label(self.frm, text="Fortigate API key")
        fortikey_lb.grid(row=5, column=0, sticky=tkinter.E)
        fortikey_ent = ttk.Entry(self.frm, textvariable=self.fortikey, show='*', width=20)
        fortikey_ent.grid(row=5, column=1, sticky=tkinter.W)
        fortikey_ent.config(state='disabled')

        # Button to retrieve AP information
        btn_get_info = ttk.Button(self.frm, text='Get AP information', command=self.get)
        btn_get_info.grid(row=6, column=0, sticky="", padx=6, pady=6)

        # Button to configure/update AP information
        btn_complete_info = ttk.Button(self.frm, text='Configure AP Information', command=self.put)
        btn_complete_info.grid(row=6, column=1, sticky="", padx=6, pady=6)

        # SCCD documentation section
        sccd_documentation_frame = ttk.Frame(self.frm)
        sccd_documentation_frame.grid(row=8, column=0, columnspan=2, pady=10)
        self.ap_sccd_doc_ui = AP_SCCD_Doc_UI(sccd_documentation_frame, geo_callback=self.geo_callback)

        # Status message label
        state_lb = ttk.Label(self.frm, textvariable=self.current_state)
        state_lb.grid(row=9, column=1)




def main_function(root_window, meraki_api_key, sccd_username, sccd_pass, geo_callback=None):
    """
    Entry point for the AP Management module.

    Creates and displays the AP Management GUI within the provided root window.

    Args:
        root_window: Parent Tkinter widget where the UI will be rendered
        meraki_api_key: Meraki API key for authentication
        sccd_username: SCCD username for CI configuration
        sccd_pass: SCCD password for CI configuration
        geo_callback: Optional callback function to resize the main window
    """
    gui_ap = APManagementGUI(
        root_window=root_window,
        meraki_api_key=meraki_api_key,
        sccd_username=sccd_username,
        sccd_pass=sccd_pass,
        geo_callback=geo_callback
    )  # Initialize the graphical interface
    gui_ap.draw()  # Draw the graphical interface


if __name__ == '__main__':
    print("AP Management")