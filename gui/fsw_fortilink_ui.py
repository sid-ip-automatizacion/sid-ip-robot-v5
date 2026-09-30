
"""Formulario Tkinter reutilizable basado en interfaz.jpeg.

Uso dentro de una aplicación existente:

    formulario = FortiSwitchForm(
        contenedor,
        on_submit=procesar_datos,
        managed_by_values=["Valor 1", "Valor 2"],
        owner_by_values=["Valor 1", "Valor 2"],
    )
    formulario.pack(fill="both", expand=True)

`contenedor` puede ser un Frame, una pestaña de Notebook, Tk o Toplevel.
Se crea un Frame independiente: usa pack(), grid() o place() para ubicarlo
de acuerdo con el gestor que ya utilice el contenedor. No se borran sus hijos.

El callback recibe un diccionario con seis cadenas:
    mgmt, cid, deal_code, support, managed_by, owner_by.
Los valores se entregan tal como se escribieron, sin conversión ni validación.
Los Combobox son readonly y empiezan vacíos. Las opciones las proporciona
la aplicación. Si aún no hay callback, el botón permanece deshabilitado;
se puede habilitar después con formulario.set_callback(procesar_datos).

El callback se ejecuta en el hilo de Tkinter. Cuando implementes llamadas
de red a FortiGate/SCCD, realiza ese trabajo fuera del hilo de la interfaz
y actualiza los widgets desde el hilo principal.

Importar el módulo no abre ventanas ni inicia mainloop. Para ver una demo:
    python interfaz_fortiswitch.py

Solo requiere la biblioteca estándar de Python con Tkinter instalado.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence
from tkinter import font, messagebox, ttk
from pprint import pprint

from core import FortigateSWController
from core import SCCD_CI_CONF as SCCD_CI


class FortiSwitchForm(ttk.Frame):
    """Construye el formulario en `master`; la aplicación decide su ubicación."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_submit: Callable[[dict[str, str]], None] | None = None,
        managed_by_values: Sequence[str] = (),
        owner_by_values: Sequence[str] = (),
    ) -> None:
        if on_submit is not None and not callable(on_submit):
            raise TypeError("on_submit debe ser una función o None.")
        super().__init__(master, padding=(20, 28))
        self._on_submit = on_submit
        self.variables = {
            campo: tk.StringVar(master=self)
            for campo in (
                "mgmt", "cid", "deal_code", "support", "api_key",
                "managed_by", "owner_by"
            )
        }

        self.columnconfigure(1, weight=1, uniform="campos")
        self.columnconfigure(3, weight=1, uniform="campos")
        self.rowconfigure(6, weight=1)

        self._title_font = font.nametofont("TkDefaultFont", root=self).copy()
        self._title_font.configure(weight="bold", size=18)
        self.title_label = ttk.Label(
            self,
            text="Fill in FSW information in SCCD (fortilink)",
            font=self._title_font,
            anchor="center"
        )
        self.title_label.grid(
            row=0, column=0, columnspan=4, sticky="ew", pady=(20, 30)
        )

        self.entries: dict[str, ttk.Entry] = {}
        for campo, etiqueta, fila, columna in (
            ("mgmt", "mgmt:", 1, 0),
            ("cid", "cid:", 1, 2),
            ("deal_code", "deal code:", 2, 0),
            ("support", "support:", 2, 2),
        ):
            separacion = (0, 0) if fila == 1 else (24, 0)
            ttk.Label(self, text=etiqueta).grid(
                row=fila,
                column=columna,
                sticky="e",
                padx=(16 if columna else 0, 8),
                pady=separacion,
            )
            entrada = ttk.Entry(self, textvariable=self.variables[campo], width=18)
            entrada.grid(
                row=fila, column=columna + 1, sticky="ew", pady=separacion
            )
            self.entries[campo] = entrada

        self.api_key_frame = ttk.Frame(self)
        self.api_key_frame.grid(row=3, column=0, columnspan=4, pady=(24, 0))
        ttk.Label(self.api_key_frame, text="API key:").grid(
            row=0, column=0, sticky="e", padx=(0, 8)
        )
        self.entries["api_key"] = ttk.Entry(
            self.api_key_frame,
            textvariable=self.variables["api_key"],
            width=18,
            show="*",
        )
        self.entries["api_key"].grid(row=0, column=1, sticky="ew")

        self.comboboxes: dict[str, ttk.Combobox] = {}
        for campo, etiqueta, columna, opciones in (
            ("managed_by", "managed by:", 0, managed_by_values),
            ("owner_by", "owner by:", 2, owner_by_values),
        ):
            ttk.Label(self, text=etiqueta).grid(
                row=4,
                column=columna,
                sticky="e",
                padx=(16 if columna else 0, 8),
                pady=(24, 0),
            )
            combo = ttk.Combobox(
                self,
                textvariable=self.variables[campo],
                values=tuple(opciones),
                state="readonly",
                width=18,
            )
            combo.grid(row=4, column=columna + 1, sticky="ew", pady=(24, 0))
            self.comboboxes[campo] = combo

        self.submit_button = ttk.Button(
            self, text="Document SCCD", width=24, command=self._submit
        )
        self.submit_button.grid(row=5, column=0, columnspan=4, pady=(36, 8))
        self.set_callback(on_submit)

    def get_values(self) -> dict[str, str]:
        """Devuelve una copia de los valores actuales, sin ejecutar el callback."""
        return {campo: variable.get() for campo, variable in self.variables.items()}

    def set_callback(
        self, callback: Callable[[dict[str, str]], None] | None
    ) -> None:
        """Asigna/reemplaza la función del botón; None deshabilita el botón."""
        if callback is not None and not callable(callback):
            raise TypeError("callback debe ser una función o None.")
        self._on_submit = callback
        self.submit_button.state(["!disabled"] if callback is not None else ["disabled"])

    def _submit(self) -> None:
        callback = self._on_submit
        if callback is not None:
            callback(self.get_values())


def document_fsw_sccd(datos: dict[str, str], env) -> None:

    fsw_controller = FortigateSWController(datos["mgmt"], datos["api_key"])
    fsw_info = fsw_controller.get_switches()
    #print(f"FortiSwitches encontrados: {fsw_info}")
    pprint(fsw_info)
    #print(f"Documentando en SCCD con los datos: {datos}")
    fsw_model_relation = (("S124FF", "FortiSwitch-124F-FPOE"), 
                          ("S148FF", "FortiSwitch-148F-FPOE"),
                          ("S124FP", "FortiSwitch-124F-POE"))
    fsw_data = []
    for fsw_1_info in fsw_info:
        if fsw_1_info.get("cid") and fsw_1_info.get("model_ip"):
            fsw_model = ""
            for model_firm, real_model in fsw_model_relation:
                if fsw_1_info.get("model_ip") == model_firm:
                    fsw_model = real_model
                    break
            dic_cid_related = []
            for cid_related in fsw_1_info.get("related_services_ids", []):
                dic_cid_related.append({"cid_related": cid_related, })
            for index, trunk_port  in enumerate(fsw_1_info.get("trunk_ports", [])):
                dic_cid_related[index]["port"] = trunk_port
            fsw_data.append(
                {
                    "dcn": ({"ip_dcn": datos["mgmt"], "vlan_mgmt": "NA"},),
                    "cid": fsw_1_info.get("cid", ""),
                    "vendor": "fortinet",
                    "hostname": fsw_1_info.get("hostname", ""),
                    "cids_related": ({"cid_related": datos["cid"], "port": "uplink"},
                                     ) + tuple(dic_cid_related),
                    "channels": (),
                    "dealcode": datos["deal_code"],
                    "support": datos["support"],
                    "managed_by": datos["managed_by"],
                    "device_owner": datos["owner_by"],
                    "sn": fsw_1_info.get("serial_number", ""),
                    "model": fsw_model,
                    "device": "sw"
                }
            )
        else:
            print(f"FortiSwitch con información incompleta: {fsw_1_info.get("serial_number", "")}")

    pprint(fsw_data)
    sccd_ci = SCCD_CI(env.get_user_sccd(), env.get_pass_sccd())
    sccd_ci.update_multiple_sw_rt_ci(fsw_data)


def fsw_window(root, env, geo_callback=None) -> None:
    if geo_callback:
        geo_callback("750x420")
    formulario = FortiSwitchForm(
        root,
        on_submit=lambda datos: document_fsw_sccd(datos, env),
        managed_by_values=("CW", "Customer"),
        owner_by_values=("CW", "CUSTOMER"),
    )
    formulario.pack(fill="both", expand=True)


def _demo() -> None:
    """Demostración local: muestra los valores, sin llamadas a FortiGate/SCCD."""
    root = tk.Tk()
    root.title("FortiSwitch — Document SCCD")
    root.geometry("750x420")
    root.minsize(540, 390)

    def mostrar_valores(datos: dict[str, str]) -> None:
        messagebox.showinfo(
            "Valores del formulario",
            "\n".join(f"{campo}: {valor}" for campo, valor in datos.items()),
            parent=root,
        )

    formulario = FortiSwitchForm(
        root,
        on_submit=mostrar_valores,
        managed_by_values=("CW", "Customer"),
        owner_by_values=("CW", "CUSTOMER"),
    )
    formulario.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    _demo()
