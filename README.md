# sid-ip-robot
robot de tareas de sid-ip

#############Librerias###############

Para ejecutar en python se deben incluir las siguientes librerías
- requests
- python-dotenv
- keyring
- passlib
- openpyxl
- meraki
- ninja2

******************* USER ENVIRONMENT *******************

************************************
DESCRIPCION GENERAL
************************************
Al iniciar el programa SID-IP Robot se crea una instancia del UserEnvironment desde el cual se cargan las diferentes aplicaciones.
Escrito en python con la libreria tkinter, permite cargar otras aplicaciones y manejar variables que se almacenan en el equipo
El UserEnvironment permite leer y escribir las variables que se almacenan permamentmente en el computador, como Usuarios, Contraseñas y URLs

***********************************************
REQUISITOS PARA INTEGRARSE CON USERENVIRONMENT
***********************************************
Las aplicaciones a integrar deben estar escritas en Python, la GUI debe ser hecha con la librería tkinter
Las aplicaciones deben estar escritas dentro de uno o varios módulos que puedan importarse desde otro script
Para iniciar la aplicación se debe desplegar una ventana inicial de tkinter (root_win). Esta ventana debe poder ser un frame de tkinter.
La aplicación debe tener una funcion que al ser llamada ejecute la aplicación (función inicial).
La función inicial debe aceptar como mínimo un argumento, que será la ventana inicial en que se carga la aplicación (root_win).
Opcionalmente la función inicial puede aceptar otros argumentos ademas del root_win, que serán las variable manejadas por el UserEnvironment a las que quiera acceder la aplicación
El primer argumento de la función inicial siempre debe ser el root_win

******************************
EJEMPLO APLICACION A INTEGRAR
******************************

#modulo_aplicacion.py
import tkinter

(...)

    def funcion_inicial(root_win, usuario1, contraseña1, usuario2, url1, ... ): # El nombre funcion_inicial es solo un ejemplo, puede darse cualquier nombre
                                                                          # El argumento root_win es obligatorio, los demás son opcionales y pueden tener cualquier nombre.
        (...)
		Titulo = tkinter.Label(master=root_win, test="Titulo")  # La ventana inicial de la aplicación debe usar el argumento root_win como ventana principal
		Frame1 = tkinter.Frame(master=root_win)                 # La ventana inicial de la aplicación debe usar el argumento root_win como ventana principal
		(...)
		
(...)
