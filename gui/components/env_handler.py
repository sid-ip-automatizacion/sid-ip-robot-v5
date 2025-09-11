import os
import dotenv
from pathlib import Path
from passlib.context import CryptContext

import tkinter    
from tkinter import ttk
import keyring

#Esta clase maneja las variables de ambiente y la configuracion de la aplicacion
# de la aplicacion. Se encarga de guardar las credenciales de SCCD y Meraki, y de cambiar el password de acceso a la aplicacion.

class EnvHandler:
    def __init__(self, master=None):
        self.master = master
        self.__hash_context = CryptContext(schemes=["pbkdf2_sha256"], default="pbkdf2_sha256",
                                                     pbkdf2_sha256__default_rounds=5000)  # Usado para hash del password
        self.__env_path = Path(__file__).resolve().parent.parent.parent / '.env'  # Ruta absoluta al archivo .env
        dotenv.load_dotenv(dotenv_path=self.__env_path)
        self.icon_path = Path(__file__).resolve().parent.parent.parent / 'resources' / 'icon.ico' #Ruta absoluta al archivo icon.ico


    def create_password(self):
        """
        Cambia el password de acceso a la aplicacion
        """
        print("Change password")
        def set_newpass():
            new_password = ent_newpass.get()
            if new_password == ent_confirm.get():
                hashed = self.__hash_context.hash(new_password)
                os.environ["SECRET_KEY_HASH"] = hashed
                dotenv.set_key(self.__env_path, 'SECRET_KEY_HASH', hashed)
                newpass_win.destroy()
            else:
                ent_newpass.delete(0, tkinter.END)
                ent_confirm.delete(0, tkinter.END)
                lbl_state.configure(text="Password not match")

        newpass_win = tkinter.Toplevel()
        newpass_msg = ttk.Label(newpass_win, text="Enter new password")
        newpass_msg.grid(row=0, column=0, padx=10, pady=10)
        ent_newpass = ttk.Entry(newpass_win, show="*", width=20)
        ent_newpass.grid(row=0, column=1, padx=10, pady=10)
        confirm_msg = ttk.Label(newpass_win, text="Confirm password")
        confirm_msg.grid(row=1, column=0, padx=10, pady=10)
        ent_confirm = ttk.Entry(newpass_win, show="*", width=20)
        ent_confirm.grid(row=1, column=1, padx=10, pady=10)
        btn_newpass = ttk.Button(newpass_win, text="Change password", command=set_newpass)
        btn_newpass.grid(row=2, column=0, pady=5)
        lbl_state = ttk.Label(newpass_win, text="")
        lbl_state.grid(row=3, column=0)
        newpass_win.mainloop()

    def set_sccd_credentials(self):
        """
        Guarda las credenciales de SCCD
        """
        def save_cred():
            user = ent_user.get()
            password = ent_pass.get()
            owner = ent_owner.get()
            os.environ["OWNER_SCCD"] = owner  # Guarda el usuario OWNER como variable de ambiente
            dotenv.set_key(self.__env_path, 'OWNER_SCCD', owner)  # Almacena usuario OWNER en archivo .env
            os.environ["LOGIN_USER_SCCD"] = user  # Guarda el usuario de login como variable de ambiente
            dotenv.set_key(self.__env_path, 'LOGIN_USER_SCCD', user)  # Almacena usuario de login en archivo .env
            keyring.set_password("SCCD_KEY", user, password)  # Guarda el password en el banco de contraseñas del sistema operativo
            sccd_cred_win.destroy()

        sccd_cred_win = tkinter.Toplevel()
        user_msg = ttk.Label(sccd_cred_win, text="Login User SCCD")
        user_msg.grid(row=0, column=0, padx=10, pady=10)
        ent_user = ttk.Entry(sccd_cred_win, width=20)
        ent_user.grid(row=0, column=1, padx=10, pady=10)
        pass_msg = ttk.Label(sccd_cred_win, text="Password SCCD")
        pass_msg.grid(row=1, column=0, padx=10, pady=10)
        ent_pass = ttk.Entry(sccd_cred_win, show="*", width=20)
        ent_pass.grid(row=1, column=1, padx=10, pady=10)
        owner_msg = ttk.Label(sccd_cred_win, text="Owner Person SCCD")
        owner_msg.grid(row=2, column=0, padx=10, pady=10)
        ent_owner = ttk.Entry(sccd_cred_win, width=20)
        ent_owner.insert(tkinter.END, ent_user.get())
        ent_owner.grid(row=2, column=1, padx=10, pady=10)
        btn_save = ttk.Button(sccd_cred_win, text="Save Credentials", command=save_cred)
        btn_save.grid(row=3, column=0, pady=5)
        sccd_cred_win.mainloop()

    def set_meraki_key(self):
        """
        Guarda la API key de Meraki
        """
        def save_cred():
            user_meraki = ent_user.get()
            meraki_key = ent_key.get()
            dotenv.set_key(self.__env_path, 'LOGIN_USER_MERAKI', user_meraki)  # Almacena usuario de login en archivo .env
            keyring.set_password("MERAKI_API_KEY", user_meraki, meraki_key)  # Guarda el password en el banco de contraseñas del sistema operativo
            sccd_cred_win.destroy()

        sccd_cred_win = tkinter.Toplevel()
        user_msg = ttk.Label(sccd_cred_win, text="Meraki user")
        user_msg.grid(row=0, column=0, padx=10, pady=10)
        ent_user = ttk.Entry(sccd_cred_win, width=20)
        ent_user.grid(row=0, column=1, padx=10, pady=10)
        key_msg = ttk.Label(sccd_cred_win, text="Meraki api keyring")
        key_msg.grid(row=1, column=0, padx=10, pady=10)
        ent_key = ttk.Entry(sccd_cred_win, show="*", width=20)
        ent_key.grid(row=1, column=1, padx=10, pady=10)
        btn_save = ttk.Button(sccd_cred_win, text="Save Meraki Auth", command=save_cred)
        btn_save.grid(row=2, column=0, pady=5)
        sccd_cred_win.mainloop()

    def get_user_sccd(self):
        """
        Obtiene el usuario de SCCD desde las variables de entorno
        :return: Usuario de SCCD
        """
        return os.environ["LOGIN_USER_SCCD"]

    def get_user_meraki(self):
        """
        Obtiene el usuario de meraki desde las variables de entorno
        :return: Usuario de meraki
        """
        return os.environ["LOGIN_USER_MERAKI"]

    def get_pass_sccd(self):
        """
        Obtiene la contraseña de SCCD desde el banco de contraseñas del sistema operativo
        :return: Contraseña de SCCD
        """
        return keyring.get_password("SCCD_KEY", self.get_user_sccd())

    def get_key_meraki(self):
        """
        Obtiene la API key de Meraki desde el banco de contraseñas del sistema operativo
        :return: API Key para meraki
        """
        return keyring.get_password("MERAKI_API_KEY", self.get_user_meraki())

    def get_owner_sccd(self):
        """
        Obtiene el owner de SCCD desde las variables de entorno
        :return: Owner de SCCD
        """
        return os.environ["OWNER_SCCD"]

    def get_urlsccd(self):
        """
        Obtiene la url de sccd
        :return: URL para los request a SCCD
        """
        return os.environ["SCCD_URL"]
    
