

import dotenv
import os
from pathlib import Path
from passlib.context import CryptContext

import tkinter
from tkinter import ttk

class AuthenticatedUser:
    def __init__(self):
        self.passw =""  # Para verificar el password de la aplicacion, no el de SCCD
        self.authenticated = False  # Indica si el usuario se autentico correctamente en la aplicacion
        self.attempts = 0  # Cantidad de intentos de autenticación en la aplicacion
        self.__hash_context = CryptContext(schemes=["pbkdf2_sha256"], default="pbkdf2_sha256",
                                                     pbkdf2_sha256__default_rounds=5000)  # Usado para hash del password
        self.__env_path = Path('.') / '.env'  # Ruta a las variables de ambiente
        dotenv.load_dotenv(dotenv_path=self.__env_path)
        self.icon_path = Path(__file__).resolve().parent / 'resources' / 'icon.ico' #Ruta absoluta al archivo icon.ico


    def auth_valid(self, passw):
        """
        Valida si una contraseña presentado es correcto
        :param passw: Contraseña a validar
        :return: Verdadero si la contraseña es correcta
        """
        hash_pass = os.environ["SECRET_KEY_HASH"]
        if self.__hash_context.verify(passw, hash_pass):
            return True
        else:
            return False

    def request_authent(self):
        """
        Solicita la autenticacón del usuario en una ventana grafica
        """

        def try_aut():
            if self.attempts < 5:
                self.passw = ent_password.get()
                self.authenticated = self.auth_valid(self.passw)
                if not self.authenticated:
                    self.attempts += 1
                    ent_password.delete(0, tkinter.END)
                    lbl_state.configure(text="Try again")
                else:
                    auth_win.destroy()
            else:
                lbl_state.configure(text="Too many tries")

        auth_win = tkinter.Tk()
        auth_win.tk.call("source", "azure.tcl")
        auth_win.tk.call("set_theme", "dark")
        auth_win.title('SID-IP robot')
        auth_win.geometry("300x200")
        auth_win.iconbitmap(self.icon_path)
        auth_msg = ttk.Label(auth_win, text="Enter password")
        auth_msg.pack(pady=20)
        ent_password = ttk.Entry(auth_win, show="*", width=20)
        ent_password.pack()
        btn_cont = ttk.Button(auth_win, text="Continue", command=try_aut)
        btn_cont.pack(pady=20)
        lbl_state = ttk.Label(auth_win, text="")
        lbl_state.pack()
        auth_win.mainloop()
