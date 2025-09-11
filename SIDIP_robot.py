import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui import UserEnvironment # importa el módulo de la interfaz gráfica
from initialize import AuthenticatedUser #importa módulo de autenticacación

def main():
    auth = AuthenticatedUser()
    auth.request_authent()
    if auth.authenticated:
        UserEnvironment()
    else:
        print("Authentication failed")
        exit(1)

if __name__ == "__main__":
    main()
