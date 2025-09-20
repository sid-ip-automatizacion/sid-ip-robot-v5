import tkinter
import tkinter as tk
from tkinter import ttk


"""
Recibe la información de Organización o Dominio y ID en formato [(org,id),(),...]
Genera una lista de selección
Devuelve el id de la Organización o Dominio seleccionada
"""



def main(clients):

    class ClientSelected:
        def __init__(self):
            self.name = ''
            self.clientID = ''

        def select_client(self, name, id_client):
            self.name = name
            self.clientID = id_client
            select_win.quit()

    list_button_clients = []

    def search_client(event):
        cadena = search_text.get("1.0", "end").replace("\n", "").lower()
        for i in range(len(list_button_clients)):
            if len(cadena) >= 3 and cadena in list_button_clients[i]["text"].lower():
                list_button_clients[i].config(bg='yellow')
            else:
                list_button_clients[i].config(bg='white smoke')
    def frame_configure(event):
        my_canvas.config(width=event.width, height=event.height)
        select_win.update_idletasks()
        my_canvas.configure(scrollregion=my_canvas.bbox(windows_item))
    select_win = tkinter.Tk()
    select_win.geometry('800x600')
    select_win.title('Select client')
    main_frame = tkinter.Frame(select_win)
    main_frame.pack(fill=tkinter.BOTH, expand=True)
    main_frame.rowconfigure(0, weight=1, minsize=10)
    main_frame.rowconfigure(1, weight=1, minsize=5)
    main_frame.columnconfigure(0, weight=1, minsize=10)
    main_frame.columnconfigure(1, weight=1, minsize=5)
    my_canvas = tkinter.Canvas(main_frame)
    scrollbar_vertical = ttk.Scrollbar(main_frame, orient='vertical', command=my_canvas.yview)
    scrollbar_horizontal = ttk.Scrollbar(main_frame, orient='horizontal', command=my_canvas.xview)
    work_area = tkinter.Frame(master=my_canvas, padx=10, pady=10)
    windows_item = my_canvas.create_window((0, 0), window=work_area, anchor='nw')
    main_frame.bind('<Configure>', frame_configure)
    my_canvas.configure(yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set)
    my_canvas.grid(row=0, column=0, sticky='nsew')
    scrollbar_horizontal.grid(row=1, column=0, sticky="ew", ipadx=10, ipady=10)
    scrollbar_vertical.grid(row=0, column=1, sticky="ns", ipadx=10, ipady=10)

    client = ClientSelected()
    work_area.columnconfigure(0, weight=1, minsize=40)
    work_area.columnconfigure(1, weight=1, minsize=10)
    work_area.rowconfigure(0, weight=1, minsize=2)
    work_area.rowconfigure(1, weight=1, minsize=10)
    sel_frame_right = tkinter.Frame(master=work_area)
    sel_frame_left = tkinter.Frame(master=work_area, bg='white smoke')
    sel_frame_right.grid(row=0, column=1, padx=(3, 0), sticky="n")
    sel_frame_left.grid(row=0, column=0, sticky="nsew")

    sel_frame_left.rowconfigure(0, weight=1, minsize=10)
    sel_frame_left.columnconfigure(0, weight=1, minsize=20)

    for count, clint in enumerate(clients):
        select_win.rowconfigure(count, weight=1, minsize=1)
        but_client_name = tkinter.Button(master=sel_frame_left, text=clint[0], height=1,
                                        command=lambda name=clint[0], id_client=clint[1]: client.select_client(name,id_client))
        but_client_name.grid(row=count, column=0, sticky="ew")
        list_button_clients.append(but_client_name)

    sel_frame_right.columnconfigure(0, weight=1, minsize=10)
    sel_frame_right.columnconfigure(1, weight=1, minsize=10)
    sel_frame_right.rowconfigure(0, weight=1, minsize=10)

    # search_text
    searchlabel = tkinter.Label(master=sel_frame_right, text="Search: ")
    searchlabel.grid(row=0, column=0, sticky="n")
    search_text = tkinter.Text(master=sel_frame_right, width=15, height=1)
    search_text.grid(row=0, column=1, sticky="n")
    search_text.bind('<KeyRelease>', search_client)

    select_win.mainloop()
    select_win.destroy()
    return client.clientID


#Pendiente PPO
class Client_Options(tk.Toplevel):
    def __init__(self, parent, clients):
        super().__init__(parent)
        self.title("Select Client")
        self.geometry('300x100')
        self.client_id = None

        label = tk.Label(self, text="Select a client:")
        label.pack(pady=10)

        self.clients = clients
        self.client_var = tk.StringVar()
        client_names = [client[0] for client in clients]
        self.client_dropdown = ttk.Combobox(self, textvariable=self.client_var, values=client_names, state="readonly")
        self.client_dropdown.pack(pady=5)

        select_button = tk.Button(self, text="Select", command=self.select_client)
        select_button.pack(pady=10)

    def select_client(self):
        selected_name = self.client_var.get()
        for client in self.clients:
            if client[0] == selected_name:
                self.client_id = client[1]
                break
        self.destroy()