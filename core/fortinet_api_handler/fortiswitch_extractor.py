"""Extrae inventario de /api/v2/monitor/switch-controller/managed-switch/status.

Python 3.10+. Sin dependencias externas para transformar el JSON.

Uso con una respuesta de requests ya obtenida:
    response.raise_for_status()
    inventario = extraer_fortiswitches(response.json())

Acepta un objeto API con `results`, o una lista de esos objetos (como sample.txt).
Devuelve siempre una lista: un diccionario por FortiSwitch, con seis campos.
No realiza solicitudes de red ni modifica archivos.

Reglas:
- El CID se reconoce por su formato, no mediante un catálogo de países.
- Conserva el orden de switches y puertos de la respuesta.
- related_services_ids[i] corresponde a trunk_ports[i]. Si dos puertos tienen
  el mismo vecino, su CID se repite para no perder la correspondencia.
- Solo usa isl_peer_device_name; no incluye fgt_peer_device_name.
- No filtra por estado del puerto ni por fortilink_port.
- Si falta CID/hostname/serial/os_version, conserva el switch con None en el
  campo correspondiente. En JSON, None se convierte en null.
- Sin vecinos con CID devuelve listas vacías. Si un vecino con CID no tiene
  interfaz local, rechaza la entrada para no inventar una relación.
- Rechaza respuestas fallidas, estructuras inválidas y hostnames ambiguos
  que contengan más de un CID.
"""

import re
from typing import Any


# Los límites permiten separadores como '_' y '-', pero evitan extraer una
# coincidencia parcial dentro de otro identificador alfanumérico o con puntos.
CID_PATTERN = re.compile(
    r"(?<![A-Za-z0-9.])([0-9]+(?:\.[0-9]+)*\.[A-Za-z]{2})(?![A-Za-z0-9.])"
)


def extraer_cid(hostname: str | None) -> str | None:
    """Extrae, por ejemplo, 42756493.1.1.CO, 38580257.1.CO o 7017667.DR."""
    if hostname is None:
        return None
    if not isinstance(hostname, str):
        raise ValueError("El hostname debe ser una cadena o null.")
    coincidencias = CID_PATTERN.findall(hostname)
    if len(coincidencias) > 1:
        raise ValueError("Hostname ambiguo: contiene más de un CID.")
    return coincidencias[0] if coincidencias else None


def _texto_opcional(objeto: dict, campo: str) -> str | None:
    valor = objeto.get(campo)
    if valor is not None and not isinstance(valor, str):
        raise ValueError(f"El campo {campo!r} debe ser una cadena o null.")
    return valor if valor and valor.strip() else None


def extraer_fortiswitches(payload: dict | list) -> list[dict[str, Any]]:
    """Transforma el resultado de response.json() usando únicamente sus datos."""
    if not isinstance(payload, (dict, list)):
        raise ValueError("Se esperaba un objeto API o una lista de objetos API.")
    respuestas = payload if isinstance(payload, list) else [payload]
    inventario = []

    for indice, respuesta in enumerate(respuestas):
        if not isinstance(respuesta, dict):
            raise ValueError(f"La respuesta {indice} no es un objeto API.")
        if respuesta.get("status") not in (None, "success"):
            raise ValueError(f"La respuesta API {indice} no indica éxito.")
        http_status = respuesta.get("http_status")
        if isinstance(http_status, int) and http_status >= 400:
            raise ValueError(f"La respuesta API {indice} indica HTTP {http_status}.")
        if not isinstance(respuesta.get("results"), list):
            raise ValueError(f"La respuesta API {indice} requiere results como lista.")

        for switch in respuesta["results"]:
            if not isinstance(switch, dict):
                raise ValueError("Cada elemento de results debe ser un objeto.")
            hostname = _texto_opcional(switch, "switch-id")
            os_version = _texto_opcional(switch, "os_version")
            puertos = switch.get("ports")
            if puertos is None:
                puertos = []
            if not isinstance(puertos, list):
                raise ValueError("El campo ports debe ser una lista o null.")

            related_services_ids = []
            trunk_ports = []

            for puerto in puertos:
                if not isinstance(puerto, dict):
                    raise ValueError("Cada elemento de ports debe ser un objeto.")
                vecino = _texto_opcional(puerto, "isl_peer_device_name")
                cid_vecino = extraer_cid(vecino)
                if cid_vecino is None:
                    continue

                interfaz = _texto_opcional(puerto, "interface")
                if interfaz is None:
                    raise ValueError("Un vecino con CID no tiene interface local.")
                related_services_ids.append(cid_vecino)
                trunk_ports.append(interfaz)

            inventario.append({
                "cid": extraer_cid(hostname),
                "hostname": hostname,
                "serial_number": _texto_opcional(switch, "serial"),
                "model_ip": os_version.split("-", 1)[0] if os_version else None,
                "related_services_ids": related_services_ids,
                "trunk_ports": trunk_ports,
            })

    return inventario
