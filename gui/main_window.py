from pathlib import Path


import tkinter    
from tkinter import ttk

from core.sccd_connector import SCCD

from .components.utils import error_window
from .components import EnvHandler 

from . import ap_management_ui as ap_mgmt
from . import sw_meraki_atp_ui as sw_m_atp
from .sccd_mgmt.sccd_manager import run_sccd_manager


class UserEnvironment:
    """
    Clase que representa el ambiente grafico del usuario.
    """
    def __init__(self):
        self.env = EnvHandler()  # Crea el manejador de variables de ambiente
        self.icon_path = Path(__file__).resolve().parent.parent / 'resources' / 'icon.ico' #Ruta absoluta al archivo icon.ico


        self.theme_path = Path(__file__).resolve().parent.parent  / 'resources' / 'azure.tcl' #Ruta absoluta al archivo azure.tcl
        """
        Crea la ventana GUI donde se ejecutara el programa
        """
        self.__root = tkinter.Tk()  # Ventana principal
        self.__root.geometry("450x350")
        self.__root.title('SID IP robot')
        self.__root.iconbitmap(self.icon_path)
        self.__root.tk.call("source", self.theme_path)
        self.__root.tk.call("set_theme", "dark")

        self.__main_frame = tkinter.Frame(self.__root)
        self.__main_frame.pack(fill=tkinter.BOTH, expand=True)
        self.__main_frame.rowconfigure(0, weight=1, minsize=10)
        self.__main_frame.rowconfigure(1, weight=1, minsize=5)
        self.__main_frame.columnconfigure(0, weight=1, minsize=10)
        self.__main_frame.columnconfigure(1, weight=1, minsize=5)
        self.__my_canvas = tkinter.Canvas(self.__main_frame)
        self.scrollbar_vertical = ttk.Scrollbar(self.__main_frame, orient='vertical', command=self.__my_canvas.yview)
        scrollbar_horizontal = ttk.Scrollbar(self.__main_frame, orient='horizontal', command=self.__my_canvas.xview)
        self.__work_area = ttk.Frame(master=self.__my_canvas, padding=(10, 10))  # Area de trabajo
        self.__windows_item = self.__my_canvas.create_window((0, 0), window=self.__work_area, anchor="nw")
        self.__main_frame.bind('<Configure>', self.frame_configure)
        self.__my_canvas.configure(yscrollcommand=self.scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)
        self.__my_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew", ipadx=10, ipady=10)
        self.scrollbar_vertical.grid(row=0, column=1, sticky="ns", ipadx=10, ipady=10)
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))
        self.__work_area.bind('<Configure>', self.working_area_configure)

        ## Barra de menu ##
        self.menubar = tkinter.Menu(self.__root)
        self.__root.config(menu=self.menubar)
        # Menu Archivo
        self.filemenu = tkinter.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Minimize", command=lambda: self.__root.iconify())
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close", command=lambda: self.__root.destroy())
        # Menu Mi cuenta
        self.myaccmenu = tkinter.Menu(self.menubar, tearoff=0)
        self.myaccmenu.add_command(label="Configure SCCD", command=self.env.set_sccd_credentials)
        self.myaccmenu.add_command(label="Change password", command=self.env.create_password)
        self.myaccmenu.add_command(label="Configure Meraki API Key", command=self.env.set_meraki_key)
        # Menu Funciones
        self.funmenu = tkinter.Menu(self.menubar, tearoff=0)
        """
        Se eliminan opciones del menu funciones para evitar que el usuario pueda abrir sccd_manager desde el menú
        self.funmenu.add_command(label="SCCD Management", command=self.run_states)
        self.funmenu.add_command(label="AP Management", command=self.run_aps)
        self.funmenu.add_command(label="Meraki SW ATP", command=self.run_atp_sw)
        self.funmenu.add_separator()
        """
        self.funmenu.add_command(label="Return to init", command=self.initial_work_area)
        # Menu Acerca de
        self.infomenu = tkinter.Menu(self.menubar, tearoff=0)
        self.infomenu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="File", menu=self.filemenu)  # Inserta menu Archivo
        self.menubar.add_cascade(label="My account", menu=self.myaccmenu)  # Inserta menu Mi cuenta
        self.menubar.add_cascade(label="Functions", menu=self.funmenu)  # Inserta menu Funciones
        self.menubar.add_cascade(label="Info", menu=self.infomenu)  # Inserta menu Info

        self.child_ref_sccd_m = False 


        self.initial_work_area()  # Dibuja la ventana inicial del area de trabajo


    def frame_configure(self, event):
        self.__my_canvas.config(width=event.width, height=event.height)
        self.__root.update_idletasks()
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))
    def working_area_configure(self, event):
        self.__root.update_idletasks()
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))

    def run_states(self):
        """
        Abre la aplicación de sccd_manager para actualizar estados y logs
        """
        
        # Ejecuta la funcion de manejo de estados en el ambiente del usuario
        # retorna una referencia a la ventana hija
        sccd = SCCD(self.env.get_owner_sccd(), self.env.get_user_sccd(), self.env.get_pass_sccd())
        
        if self.env.get_owner_sccd() == '' or self.env.get_user_sccd() == '' or self.env.get_pass_sccd() == '':
            print("SCCD credentials are not set")
            self.env.set_sccd_credentials()
            self.btn_sccd_m.config(state="normal")  # Habilita el boton si no se pudo abrir la ventana hija
        elif sccd.validate_credentials.status_code == 401:
            print("SCCD credentials are not valid")
            self.env.set_sccd_credentials()
            self.btn_sccd_m.config(state="normal")  # Habilita el boton si no se pudo abrir la ventana hija
        elif sccd.validate_credentials.status_code == 200:
            self.btn_sccd_m.config(state="disabled")  # Deshabilita el boton mientras se ejecuta la función
            self.child_ref_sccd_m = True
            run_sccd_manager(self.env.get_owner_sccd(), 
                            self.env.get_user_sccd(), 
                            self.env.get_pass_sccd(), 
                            on_close=self._child_closed_sccd_m)  # Pasa el callback de cierre de la ventana hija
        else:
            error_window("Error connecting to SCCD, please try again later.")
            print("Error connecting to SCCD, status code:", sccd.validate_credentials.status_code) 
            self.btn_sccd_m.config(state="normal")  # Habilita el boton si no se pudo abrir la ventana hija


    def run_aps(self):
        """
        Carga la ventana de manejo de APs
        """
        self.clear_work_area()  # Limpia el area de trabajo
        ap_mgmt.main_function(self.get_work_area(), self.env.get_key_meraki())  # Ejecuta el manejo de APs en el ambiente del usuario

    def run_atp_sw(self):
        """
        Carga la ventana de ATP de SW 
        """
        self.clear_work_area()  # Limpia el area de trabajo
        sw_m_atp.main_function(self.get_work_area(), self.env.get_key_meraki())  # Ejecuta la venta  de ATP switches en el ambiente usuario

    def initial_work_area(self):
        """
        Dibuja  la ventana inicial del area de trabajo con los tres botones principales
        1. SCCD Management
        2. AP Management
        3. Meraki SW ATP
        """
        self.clear_work_area()  # Limpia el area de trabajo
        self.btn_sccd_m = ttk.Button(master=self.get_work_area(), text="SCCD Management", command=self.run_states)
        self.btn_aps = ttk.Button(master=self.get_work_area(), text="AP Management", command=self.run_aps)
        self.btn_sw_atp = ttk.Button(master=self.get_work_area(), text="Meraki SW ATP", command=self.run_atp_sw)
        self.btn_sccd_m.pack(side="top", padx=12, pady=12)
        self.btn_aps.pack(side="top", padx=12, pady=12)
        self.btn_sw_atp.pack(side="top", padx=12, pady=12)

        if self.child_ref_sccd_m:
            self.btn_sccd_m.config(state="disabled")  # Deshabilita el boton si la ventana hija sigue abierta
        self.__root.mainloop()

    def adjust_window(self, window):
        """
        Aumenta el tamaño de un marco GUI al tamaño de la ventana
        :param window: Ventana que se quiere ajustar
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
        self.__my_canvas.update_idletasks()
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))
        self.__my_canvas.configure(scrollregion=self.__my_canvas.bbox(self.__windows_item))

    def clear_work_area(self):
        """
        Limpia el area de trabajo
        """
        for widgets in self.__work_area.winfo_children():
            widgets.destroy()

    def get_root_window(self):
        return self.__root

    def get_work_area(self):
        return self.__work_area
    
    def _child_closed_sccd_m(self):
        self.btn_sccd_m.config(state="normal")  # Habilita el boton cuando se cierra la ventana hija
        self.child_ref_sccd_m = False
    

    def show_about(self):
        """
        Muestra la ventana Acerca de"
        """
        about_win = tkinter.Toplevel()
        about_text = tkinter.Label(about_win, text='version: 5.0.10'
                                                   '\nSID-IP release'
                                                  '\n\nDesarrollado por SID-IP Team, Liberty Networks'
                                                  '\nEquipo de desarrollo:'
                                                  '\nAlvaro Molano, Cesar Castillo, Nicole Paz, '
                                                  '\nWilliam Galindo, Luis Solís',)
        about_text.grid(row=0, column=0)
        about_win.title('About:')
        about_win.iconbitmap(self.icon_path)
        about_win.mainloop()
