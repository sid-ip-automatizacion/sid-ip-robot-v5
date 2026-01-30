"""
Environment Handler Module.

This module provides the EnvHandler class for managing application configuration,
environment variables, and secure credential storage. It handles SCCD and Meraki
credentials using a combination of .env files and the OS keyring.
"""

import os
import sys
import dotenv
from pathlib import Path
from passlib.context import CryptContext

import tkinter
from tkinter import ttk
import keyring


class EnvHandler:
    """
    Environment and credential manager for the application.

    Handles saving and retrieving SCCD and Meraki credentials, and manages
    the application access password. Uses:
    - .env file for non-sensitive configuration (usernames)
    - OS keyring for secure password/API key storage
    - passlib for password hashing

    Attributes:
        master: Optional Tkinter master widget
        icon_path (Path): Path to the application icon
        BASE_DIR (Path): Base directory for the application
    """

    def __init__(self, master=None):
        """
        Initialize the EnvHandler.

        Args:
            master: Optional Tkinter master widget
        """
        self.master = master
        # Hash context for password hashing using PBKDF2-SHA256
        self.__hash_context = CryptContext(
            schemes=["pbkdf2_sha256"],
            default="pbkdf2_sha256",
            pbkdf2_sha256__default_rounds=5000
        )

        # Absolute path to icon.ico file
        self.icon_path = Path(__file__).resolve().parent.parent.parent / 'resources' / 'icon.ico'

        self.BASE_DIR: Path = self.app_base_dir()
        self.__env_path: Path = self.BASE_DIR / ".env"
        dotenv.load_dotenv(dotenv_path=self.__env_path)

    def app_base_dir(self) -> Path:
        """
        Get the application base directory.

        Returns:
            Path: Base directory path
                - For .exe (PyInstaller): folder containing the executable
                - For dev: project root (../../ from this file)
        """
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        # This file is in gui/components/, go up two levels to repo root
        return Path(__file__).resolve().parents[2]

    def resource_path(self, relative: str) -> str:
        """
        Get the path to bundled or local resources.

        Useful for accessing icons and other assets in both development
        and PyInstaller-bundled environments.

        Args:
            relative: Relative path to the resource

        Returns:
            str: Absolute path to the resource
        """
        base = getattr(sys, "_MEIPASS", str(self.BASE_DIR))
        return str((Path(base) / relative).resolve())

    def create_password(self) -> None:
        """
        Open a dialog to change the application access password.

        Creates a Toplevel window prompting for new password with confirmation.
        The password is hashed using PBKDF2-SHA256 and stored in .env file.
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

    def set_sccd_credentials(self) -> None:
        """
        Open a dialog to configure SCCD credentials.

        Creates a Toplevel window prompting for:
        - Login username (stored in .env)
        - Password (stored in OS keyring)
        - Owner person (stored in .env)
        """
        def save_cred():
            user = ent_user.get()
            password = ent_pass.get()
            owner = ent_owner.get()
            # Save OWNER username as environment variable
            os.environ["OWNER_SCCD"] = owner
            # Store OWNER username in .env file
            dotenv.set_key(self.__env_path, 'OWNER_SCCD', owner)
            # Save login username as environment variable
            os.environ["LOGIN_USER_SCCD"] = user
            # Store login username in .env file
            dotenv.set_key(self.__env_path, 'LOGIN_USER_SCCD', user)
            # Save password in OS keyring
            keyring.set_password("SCCD_KEY", user, password)
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

    def set_meraki_key(self) -> None:
        """
        Open a dialog to configure Meraki API credentials.

        Creates a Toplevel window prompting for:
        - Meraki username (stored in .env)
        - API key (stored in OS keyring)
        """
        def save_cred():
            user_meraki = ent_user.get()
            meraki_key = ent_key.get()
            # Store login username in .env file
            dotenv.set_key(self.__env_path, 'LOGIN_USER_MERAKI', user_meraki)
            # Save API key in OS keyring
            keyring.set_password("MERAKI_API_KEY", user_meraki, meraki_key)
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

    def get_user_sccd(self) -> str:
        """
        Get the SCCD login username from environment variables.

        Returns:
            str: SCCD login username
        """
        return os.environ["LOGIN_USER_SCCD"]

    def get_user_meraki(self) -> str:
        """
        Get the Meraki username from environment variables.

        Returns:
            str: Meraki username
        """
        return os.environ["LOGIN_USER_MERAKI"]

    def get_pass_sccd(self) -> str:
        """
        Get the SCCD password from the OS keyring.

        Returns:
            str: SCCD password
        """
        return keyring.get_password("SCCD_KEY", self.get_user_sccd())

    def get_key_meraki(self) -> str:
        """
        Get the Meraki API key from the OS keyring.

        Returns:
            str: Meraki API key
        """
        return keyring.get_password("MERAKI_API_KEY", self.get_user_meraki())

    def get_owner_sccd(self) -> str:
        """
        Get the SCCD owner person from environment variables.

        Returns:
            str: SCCD owner username
        """
        return os.environ["OWNER_SCCD"]

    def get_urlsccd(self) -> str:
        """
        Get the SCCD base URL from environment variables.

        Returns:
            str: SCCD API base URL
        """
        return os.environ["SCCD_URL"]
