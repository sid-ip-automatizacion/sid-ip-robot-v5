"""
Main Window Module for SID-IP Robot.

This module provides the UserEnvironment class which serves as the main
graphical interface for the application. It manages the main window,
menu bar, and provides a scrollable work area where different application
modules can be loaded.
"""

from pathlib import Path

import tkinter
from tkinter import ttk

from core import SCCD_WO as SCCD

from .components.utils import error_window
from .components import EnvHandler

from . import ap_management_ui as ap_mgmt
from . import sw_meraki_atp_ui as sw_m_atp
from .sccd_mgmt.sccd_manager import run_sccd_manager
from .sccd_mgmt.m_asset_assig import main_function as maa_function
from .sccd_mgmt.back_office_mgmt import main_function as bo_function


class UserEnvironment:
    """
    Main application window and user environment manager.

    This class creates and manages the main GUI window with a scrollable
    work area where different application modules are loaded. It handles
    the menu bar, credential management, and module navigation.

    Attributes:
        env (EnvHandler): Environment handler for credentials and settings
        icon_path (Path): Path to the application icon
        theme_path (Path): Path to the Azure theme file
        child_ref_sccd_m (bool): Flag indicating if SCCD manager child window is open
    """

    def __init__(self):
        """
        Initialize the UserEnvironment and create the main window.

        Sets up the main Tkinter window with:
        - Azure dark theme
        - Scrollable canvas work area
        - Menu bar with File, My account, Functions, and Info menus
        """
        self.env = EnvHandler()  # Create environment handler
        # Absolute path to icon.ico file
        self.icon_path = Path(__file__).resolve().parent.parent / 'resources' / 'icon.ico'
        # Absolute path to azure.tcl theme file
        self.theme_path = Path(__file__).resolve().parent.parent / 'resources' / 'azure.tcl'

        # Create the main GUI window
        self.__root = tkinter.Tk()
        self.__root.geometry("250x400")
        self.__root.title('SID IP robot')
        self.__root.iconbitmap(self.icon_path)
        self.__root.tk.call("source", self.theme_path)
        self.__root.tk.call("set_theme", "dark")

        # Configure main frame with scrollable canvas
        self.__main_frame = tkinter.Frame(self.__root)
        self.__main_frame.pack(fill=tkinter.BOTH, expand=True)
        self.__main_frame.rowconfigure(0, weight=1, minsize=10)
        self.__main_frame.rowconfigure(1, weight=1, minsize=5)
        self.__main_frame.columnconfigure(0, weight=1, minsize=10)
        self.__main_frame.columnconfigure(1, weight=1, minsize=5)

        self.__my_canvas = tkinter.Canvas(self.__main_frame)
        self.scrollbar_vertical = ttk.Scrollbar(
            self.__main_frame, orient='vertical', command=self.__my_canvas.yview)
        scrollbar_horizontal = ttk.Scrollbar(
            self.__main_frame, orient='horizontal', command=self.__my_canvas.xview)

        # Work area frame inside the canvas
        self.__work_area = ttk.Frame(master=self.__my_canvas, padding=(10, 10))
        self.__windows_item = self.__my_canvas.create_window(
            (0, 0), window=self.__work_area, anchor="nw")

        # Configure scroll bindings
        self.__main_frame.bind('<Configure>', self.frame_configure)
        self.__my_canvas.configure(
            yscrollcommand=self.scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set)
        self.__my_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew", ipadx=10, ipady=10)
        self.scrollbar_vertical.grid(row=0, column=1, sticky="ns", ipadx=10, ipady=10)
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))
        self.__work_area.bind('<Configure>', self.working_area_configure)

        # ---------- Menu Bar Setup ----------
        self.menubar = tkinter.Menu(self.__root)
        self.__root.config(menu=self.menubar)

        # File menu
        self.filemenu = tkinter.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Minimize", command=lambda: self.__root.iconify())
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close", command=lambda: self.__root.destroy())

        # My Account menu
        self.myaccmenu = tkinter.Menu(self.menubar, tearoff=0)
        self.myaccmenu.add_command(label="Configure SCCD", command=self.env.set_sccd_credentials)
        self.myaccmenu.add_command(label="Change password", command=self.env.create_password)
        self.myaccmenu.add_command(label="Configure Meraki API Key", command=self.env.set_meraki_key)

        # Functions menu
        self.funmenu = tkinter.Menu(self.menubar, tearoff=0)
        # Note: Direct menu access to modules disabled to enforce main menu navigation
        self.funmenu.add_command(label="Return to menu", command=self.initial_work_area)

        # Info menu
        self.infomenu = tkinter.Menu(self.menubar, tearoff=0)
        self.infomenu.add_command(label="About", command=self.show_about)

        # Add menus to menu bar
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.menubar.add_cascade(label="My account", menu=self.myaccmenu)
        self.menubar.add_cascade(label="Functions", menu=self.funmenu)
        self.menubar.add_cascade(label="Info", menu=self.infomenu)

        self.child_ref_sccd_m = False

        # Draw initial work area with main menu buttons
        self.initial_work_area()

    def frame_configure(self, event):
        """Handle main frame resize events and update canvas scroll region."""
        self.__my_canvas.config(width=event.width, height=event.height)
        # Expand work area to fill canvas width so buttons stay centered
        self.__my_canvas.itemconfig(self.__windows_item, width=event.width)
        self.__root.update_idletasks()
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))

    def working_area_configure(self, event):
        """Handle work area resize events and update canvas scroll region."""
        self.__root.update_idletasks()
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))

    def run_states(self):
        """
        Open the SCCD Manager for work order state and log management.

        Validates SCCD credentials before launching. If credentials are
        missing or invalid, prompts user to configure them.
        """
        # Execute state management function in user environment
        sccd = SCCD(self.env.get_owner_sccd(),
                    self.env.get_user_sccd(),
                    self.env.get_pass_sccd())

        if (self.env.get_owner_sccd() == '' or
                self.env.get_user_sccd() == '' or
                self.env.get_pass_sccd() == ''):
            print("SCCD credentials are not set")
            self.env.set_sccd_credentials()
            # Re-enable button if child window couldn't open
            self.btn_sccd_m.config(state="normal")
        elif sccd.validate_credentials.status_code == 401:
            print("SCCD credentials are not valid")
            self.env.set_sccd_credentials()
            # Re-enable button if child window couldn't open
            self.btn_sccd_m.config(state="normal")
        elif sccd.validate_credentials.status_code == 200:
            # Disable button while function is running
            self.btn_sccd_m.config(state="disabled")
            self.child_ref_sccd_m = True
            run_sccd_manager(
                self.env.get_owner_sccd(),
                self.env.get_user_sccd(),
                self.env.get_pass_sccd(),
                on_close=self._child_closed_sccd_m  # Pass child window close callback
            )
        else:
            error_window("Error connecting to SCCD, please try again later.")
            print("Error connecting to SCCD, status code:",
                  sccd.validate_credentials.status_code)
            # Re-enable button if child window couldn't open
            self.btn_sccd_m.config(state="normal")

    def run_aps(self):
        """Load the AP Management interface into the work area."""
        self.clear_work_area()
        ap_mgmt.main_function(
            root_window=self.get_work_area(),
            meraki_api_key=self.env.get_key_meraki(),
            sccd_username=self.env.get_user_sccd(),
            sccd_pass=self.env.get_pass_sccd(),
            geo_callback=self.geometry
        )

    def run_atp_sw(self):
        """Load the Meraki Switch ATP interface into the work area."""
        self.clear_work_area()
        sw_m_atp.main_function(self.get_work_area(), self.env.get_key_meraki())

    def run_multi_asset_assignment(self):
        """Load the Multi-Asset Assignment interface into the work area."""
        self.clear_work_area()
        maa_function(
            self.get_work_area(),
            self.env.get_owner_sccd(),
            self.env.get_user_sccd(),
            self.env.get_pass_sccd()
        )

    def run_bo_mgmt(self):
        """Load the Back Office Management interface into the work area."""
        self.clear_work_area()
        bo_function(
            self.get_work_area(),
            self.env.get_user_sccd(),
            self.env.get_pass_sccd(),
            geo_callback=self.geometry
        )

    def initial_work_area(self):
        """
        Draw the initial work area with main menu buttons.

        Creates buttons for:
        1. SCCD WO Management
        2. AP Management
        3. Meraki SW ATP
        4. SCCD Multi-Asset Assignment
        5. Back Office Management
        """
        self.clear_work_area()
        self.__root.geometry("250x400")

        self.btn_sccd_m = ttk.Button(
            master=self.get_work_area(),
            text="SCCD WO Management",
            command=self.run_states
        )
        self.btn_aps = ttk.Button(
            master=self.get_work_area(),
            text="AP Management",
            command=self.run_aps
        )
        self.btn_sw_atp = ttk.Button(
            master=self.get_work_area(),
            text="Meraki SW ATP",
            command=self.run_atp_sw
        )
        self.btn_sccd_maa = ttk.Button(
            master=self.get_work_area(),
            text="SCCD Multi-Asset Assignment",
            command=self.run_multi_asset_assignment
        )
        self.btn_bo_m = ttk.Button(
            master=self.get_work_area(),
            text="Back Office Management",
            command=self.run_bo_mgmt
        )

        self.btn_sccd_m.pack(side="top", padx=12, pady=12)
        self.btn_aps.pack(side="top", padx=12, pady=12)
        self.btn_sw_atp.pack(side="top", padx=12, pady=12)
        self.btn_sccd_maa.pack(side="top", padx=12, pady=12)
        self.btn_bo_m.pack(side="top", padx=12, pady=12)

        if self.child_ref_sccd_m:
            # Disable button if child window is still open
            self.btn_sccd_m.config(state="disabled")

        # Center buttons by expanding work area to canvas width after geometry is set
        self.__root.update_idletasks()
        self.__my_canvas.itemconfig(self.__windows_item, width=self.__my_canvas.winfo_width())

        self.__root.mainloop()

    def adjust_window(self, window):
        """
        Expand the canvas item to match the window size.

        Args:
            window: The window/frame to adjust
        """
        if window.winfo_width() < self.__root.winfo_width():
            self.__root.update_idletasks()
            self.__my_canvas.itemconfig(self.__windows_item, width=self.__root.winfo_width())
            self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))
        if window.winfo_height() < self.__root.winfo_height():
            self.__root.update_idletasks()
            self.__my_canvas.itemconfig(self.__windows_item, height=self.__root.winfo_height())
            self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))

    def update_canvas(self):
        """Update the canvas scroll region."""
        self.__my_canvas.update_idletasks()
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))

    def clear_work_area(self):
        """Clear all widgets from the work area."""
        for widgets in self.__work_area.winfo_children():
            widgets.destroy()

    def get_root_window(self):
        """Return the root Tkinter window."""
        return self.__root

    def get_work_area(self):
        """Return the work area frame for loading modules."""
        return self.__work_area

    def _child_closed_sccd_m(self):
        """Callback for when the SCCD Manager child window is closed."""
        self.btn_sccd_m.config(state="normal")
        self.child_ref_sccd_m = False

    def geometry(self, size: str):
        """
        Set the main window geometry.

        Args:
            size: Window size in format "WxH" (e.g., "400x300")
        """
        self.__root.geometry(size)

    def show_about(self):
        """Display the About dialog window."""
        about_win = tkinter.Toplevel()
        about_text = tkinter.Label(
            about_win,
            text='version: 5.4.4'
                 '\nSID-IP release'
                 '\n\nDeveloped by SID-IP Team, Liberty Networks'
                 '\nDevelopment Team:'
                 '\nAlvaro Molano, Cesar Castillo, Nicole Paz, '
                 '\nWilliam Galindo, Luis Solís',
            justify="left"
        )
        about_text.grid(row=0, column=0)
        about_win.title('About:')
        about_win.iconbitmap(self.icon_path)
        about_win.mainloop()
