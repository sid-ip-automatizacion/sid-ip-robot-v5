from pathlib import Path


import tkinter    
from tkinter import ttk

from core.ap_management import get_controller
from core.ruckus import get_domains
from core.meraki import get_org

from gui.ap_sccd_doc_ui import AP_SCCD_Doc_UI
from .components import error_window, save_excel, select_client, load_excel



class APManagementGUI:    
    def __init__(self, root_window, meraki_api_key, geo_callback=None):
        self.master = root_window
        self.current_state = tkinter.StringVar()
        self.current_state.set("select vendor and fill data")
        self.vendor_selected = None
        self.login_user = tkinter.StringVar()
        self.login_pass = tkinter.StringVar()
        self.url = tkinter.StringVar()
        self.fortikey = tkinter.StringVar()

        self.geo_callback = geo_callback

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
        """
        Método para limpiar el área de trabajo.
        """
        for widget in self.master.winfo_children():
            widget.destroy()
    
    def set_controller_info(self):
        """
        Método para establecer la información del controlador.
        Este método se utiliza para actualizar la información del controlador con los datos proporcionados.
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
        """ Método para obtener la información de los puntos de acceso y se guardan en un archivo Excel.
        """
        try:
            self.set_controller_info()  # Establece la información del controlador
            controller = get_controller(self.controller_info) #Genera el controlador según la información de controller_info
            apinfo = controller.get() # Obtiene la información de los puntos de acceso
            self.current_state.set("please save the file")
            save_excel(apinfo) # Guarda la información en un archivo Excel
            self.current_state.set("file saved")
            print("File saved")
        except Exception as e:
            error_window(f"Error retrieving AP information: {e}")
            print(f"Error retrieving AP information: {e}")
            
    def put(self):
        """ Método para completar la información de name, description y address de los puntos de acceso.
        Este método se utiliza para actualizar la información de los puntos de acceso con los datos proporcionados
        """
        try:
            self.set_controller_info()  # Establece la información del controlador
            self.controller_info['ap_list'] = load_excel()  # Carga la lista de puntos de acceso desde un archivo Excel
            controller = get_controller(self.controller_info)  # Genera el controlador según la información de controller_info
            controller.put()  # Envía la información de los puntos de acceso al controlador
            self.current_state.set("AP information updated successfully")
            print("AP information updated successfully")
        except Exception as e:
            error_window(f"Error updating AP information: {e}")
            print(f"Error updating AP information: {e}")
            return


    def draw(self):
        """
        Método para dibujar la interfaz gráfica.
        Este método crea los widgets necesarios para la gestión de puntos de acceso.
        Se crea un formulario con campos para seleccionar el proveedor, ingresar credenciales y URL.
        También se incluyen botones para obtener información de los puntos de acceso y completar la información.
        Además, se muestra un mensaje de estado para informar al usuario sobre el progreso de las operaciones
        """
        def select_vendor(event):

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
        self.clear_work_area()  # Limpia el área de trabajo antes de dibujar la interfaz
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
        # Titulo

        title_lb = ttk.Label(self.frm, text="ACCESS POINTS MANAGER", anchor=tkinter.CENTER, font=('Helvetica',12))
        title_lb.grid(row=0, columnspan=2, pady=10)

        # Lista desplegable de vendors

        selected_vendor = tkinter.StringVar(self.frm)
        vendor_lb = ttk.Label(self.frm, text="Choose vendor")
        vendor_lb.grid(row=1, column=0, sticky=tkinter.E)
        cb_vendors = ttk.Combobox(self.frm, state='readonly', textvariable=selected_vendor)
        cb_vendors['values'] = ['Ruckus-SZ', 'Meraki', 'Fortinet']
        cb_vendors.grid(row=1, column=1, sticky=tkinter.W)
        cb_vendors.bind('<<ComboboxSelected>>', select_vendor)

        # Entrada para el user

        user_lb = ttk.Label(self.frm, text="Login user")
        user_lb.grid(row=2, column=0, sticky=tkinter.E)
        user_ent = ttk.Entry(self.frm, textvariable=self.login_user, width=20)
        user_ent.grid(row=2, column=1, sticky=tkinter.W)
        user_ent.config(state='disabled')

        # Entrada para el password

        pass_lb = ttk.Label(self.frm, text="Password")
        pass_lb.grid(row=3, column=0, sticky=tkinter.E)
        pass_ent = ttk.Entry(self.frm, show='*', textvariable=self.login_pass, width=20)
        pass_ent.grid(row=3, column=1, sticky=tkinter.W)
        pass_ent.config(state='disabled')

        # Entrada para la URL del controlador

        url_lb = ttk.Label(self.frm, text="Controller URL")
        url_lb.grid(row=4, column=0, sticky=tkinter.E)
        url_ent = ttk.Entry(self.frm, textvariable=self.url, width=20)
        url_ent.grid(row=4, column=1, sticky=tkinter.W)
        url_ent.config(state='disabled')

        # Entrada para la key fortigate

        fortikey_lb = ttk.Label(self.frm, text="Fortigate API key")
        fortikey_lb.grid(row=5, column=0, sticky=tkinter.E)
        fortikey_ent = ttk.Entry(self.frm, textvariable=self.fortikey, show='*', width=20)
        fortikey_ent.grid(row=5, column=1, sticky=tkinter.W)
        fortikey_ent.config(state='disabled')

        # Boton para seleccionar archivo a completar
        btn_get_info = ttk.Button(self.frm, text='Get AP information', command=self.get)
        btn_get_info.grid(row=6, column=0, sticky="", padx=6, pady=6)

        # Boton para generar el archivo completo
        btn_complete_info = ttk.Button(self.frm, text='Configure AP Information', command=self.put)
        btn_complete_info.grid(row=6, column=1, sticky="", padx=6, pady=6)

        # sccd documentation 
        sccd_documentation_frame = ttk.Frame(self.frm)
        sccd_documentation_frame.grid(row=8, column=0, columnspan=2, pady=10)
        ap_sccd_doc_ui = AP_SCCD_Doc_UI(sccd_documentation_frame, geo_callback=self.geo_callback)
        

        # Mensage de estado
        state_lb = ttk.Label(self.frm, textvariable=self.current_state)
        state_lb.grid(row=9, column=1)




def main_function(root_window, meraki_api_key, geo_callback=None):
    """
    Función principal que se ejecuta al iniciar el script.
    Aquí puedes agregar la lógica que deseas ejecutar.
    """
    gui_ap = APManagementGUI(root_window,meraki_api_key, geo_callback=geo_callback)  # Inicializa la interfaz gráfica
    gui_ap.draw()  # Dibuja la interfaz gráfica
    print("Función principal ejecutada.")


if __name__ == '__main__':
    # fill_AP_info('ruckus_vsz')
    # complete_mac_or_serial('ruckus_vsz', config_aps_file)
    # label_aps('ruckus_vsz', config_aps_file)
    print("AP Mangement")