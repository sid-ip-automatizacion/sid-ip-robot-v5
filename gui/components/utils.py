import tkinter
from tkinter.filedialog import asksaveasfilename, askopenfilename

import pandas as pd


def error_window(text):
        #ventana de error, recibe un texto y lo muestra en una ventana de error
        print("ERROR: {}".format(text))
        error_win = tkinter.Tk()
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
    Abre un archivo Excel y devuelve un array de diccionarios.
    • La primera fila se interpreta como cabeceras (keys).
    • Cada fila siguiente se convierte en un diccionario dentro de la lista.
    """
    file_path = askopenfilename(
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        title="Abrir archivo"
    )

    if not file_path:
        print("Lectura cancelada.")
        return []

    # Leer el Excel (pandas reconoce automáticamente las cabeceras).
    df = pd.read_excel(file_path)

    # Convertir a lista de diccionarios.
    records = df.to_dict(orient="records")
    return records