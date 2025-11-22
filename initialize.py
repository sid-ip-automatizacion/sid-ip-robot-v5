"""
Initialization and authentication module for the SID-IP robot.

This module defines the AuthenticatedUser class which handles the user
authentication process via a Tkinter graphical interface and secure
password verification.
"""

from pathlib import Path
import os
import tkinter
from tkinter import ttk

from passlib.context import CryptContext
import dotenv


class AuthenticatedUser:
    """
    Manages user authentication for the application.

    This class handles the graphical authentication window, validates passwords
    against a hashed secret, and tracks authentication state.
    """

    def __init__(self):
        self.passw = ""  # Stores the application password, not the SCCD password
        self.authenticated = False
        self.attempts = 0  # Number of authentication attempts in the application
        self.__hash_context = CryptContext(
            schemes=["pbkdf2_sha256"],
            default="pbkdf2_sha256",
            pbkdf2_sha256__default_rounds=5000)  # Used for password hashing
        self.__env_path = Path('.') / '.env'
        dotenv.load_dotenv(dotenv_path=self.__env_path)
        self.icon_path = Path(__file__).resolve().parent / \
            'resources' / 'icon.ico'

    def auth_valid(self, passw):
        """
        Validates if a provided password is correct.
        Args:
            passw (str): The password to validate.
        Returns:
            bool: True if the password is correct, False otherwise.
        """
        hash_pass = os.environ["SECRET_KEY_HASH"]
        if self.__hash_context.verify(passw, hash_pass):
            return True
        else:
            return False

    def request_authent(self):
        """
        Requests user authentication via a graphical window.

        Launches a Tkinter window prompting the user for a password.
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
        auth_win.tk.call("source", "resources/azure.tcl")
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
