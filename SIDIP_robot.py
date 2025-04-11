import UserEnvironment as ue

def authenticate(gui_env):
    """
    Autenticacion e ingreso a la aplicacion
    :param gui_env: Ambiente grafico del usuario
    """
    gui_env.request_authent()
    if gui_env.authenticated:
        gui_env.create_work_area()
        gui_env.initial_work_area()

def main():
    gui_env = ue.UserEnvironment()  # Crea el ambiente principal de la GUI
    authenticate(gui_env)


if __name__ == "__main__":
    main()
