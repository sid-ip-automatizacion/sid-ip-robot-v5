from pathlib import Path
import tkinter
from tkinter.filedialog import asksaveasfilename, askopenfilename

import pandas as pd

theme_path = Path(__file__).resolve().parent.parent.parent / 'resources' / 'azure.tcl' #Ruta absoluta al archivo azure.tcl

def error_window(text):
        #ventana de error, recibe un texto y lo muestra en una ventana de error
        print("ERROR: {}".format(text))
        error_win = tkinter.Tk()
        error_win.tk.call("source", theme_path)
        error_win.tk.call("set_theme", "dark")
        error_text = tkinter.Label(error_win, text=text)
        ok_button = tkinter.Button(error_win, text='OK', width=5, height=2, command=error_win.destroy)
        error_text.pack()
        ok_button.pack()
        error_win.mainloop()


def save_excel(datos):

    """
    Esta función recibe cualquier arreglo en formato array de diccionarios [{},{},{}...] y genera un archivo excel para ser guardado
    """

    # Crear el DataFrame
    df = pd.DataFrame(datos)
    
    # Cuadro de diálogo para guardar archivo
    file_path = asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        title="Guardar como"
    )

    if file_path:
        # Guardar el DataFrame en Excel
        df.to_excel(file_path, index=False)
        print(f"Archivo guardado en: {file_path}")
    else:
        print("Guardado cancelado.")


def load_excel():
    """
    Abre un archivo Excel y devuelve una lista de diccionarios.
    - La primera fila se interpreta como cabeceras (keys).
    - Las keys se normalizan a minúscula.
    """
    file_path = askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        title="Abrir archivo"
    )

    if not file_path:
        print("Lectura cancelada.")
        return []

    df = pd.read_excel(file_path)
    # Normaliza cabeceras: a string, sin espacios extremos y minúscula
    df.columns = [str(c).strip().lower() for c in df.columns]

    return df.to_dict(orient="records")