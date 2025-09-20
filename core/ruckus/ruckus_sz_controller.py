#!/usr/bin/env python3
"""
Requisitos:
    pip install requests urllib3
Nota: Se deshabilita temporalmente la verificación TLS (verify=False).
      No recomendado para producción.
"""

import requests
import urllib3
from pprint import pprint
from typing import Dict, List
from time import sleep

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SmartZoneAPI:
    def __init__(self, controller_url, username, password):
        self.base_url = f'https://{controller_url}/wsg/api/public/v9_1'
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = self.login()

    def login(self):
        url = f'{self.base_url}/session'
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(url, json=payload, verify=False)
        response.raise_for_status()
        token = response.json().get('token')
        self.session.headers.update({'Authorization': f'Session {token}'})
        return token
    # ------- Consulta de Domains ---------

    def get_domains(self):
        url = f'{self.base_url}/domains'
        response = self.session.get(url, verify=False)
        response.raise_for_status()
        domains_data = response.json().get('list', [])
        domains_list_dic = []
        for domain in domains_data:
            domains_list_dic.append((domain.get('name'),domain.get('id')))

        return domains_list_dic

    # ---------- Consulta de APs ----------
    def query_aps_by_domain(self, domain_id: str,
                            page_size: int = 100) -> List[Dict]:
        """
        Devuelve la lista completa de APs dentro de un dominio
        usando POST /query/ap y paginación.
        """
        print("Domain:", domain_id)
        endpoint = f"{self.base_url}/query/ap"
        page = 1
        aps: List[Dict] = []
        aps_list_dic: List[Dict] = []

        while True:
            if domain_id == '0':
                payload = {
                    "page": page,
                    "limit": page_size
                }
            else:   
                payload = {
                    "filters": [
                        {"type": "DOMAIN", "value": domain_id, "operator": "eq"}
                    ],
                    "page": page,
                    "limit": page_size
                }

            resp = self.session.post(endpoint, json=payload,
                                     verify=False, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            aps.extend(data.get("list", []))

            # ¿Hemos recibido todos los registros?
            total = data.get("totalCount", len(aps))
            if len(aps) >= total:
                break
            page += 1
        # ---------- Formateo de datos ----------
        """Extrae y normaliza los campos solicitados de la respuesta."""
        for ap in aps:
            aps_list_dic.append(
                {"name": ap.get("deviceName"),
                "model": ap.get("model"),
                "description": ap.get("description"),
                "site": ap.get("apGroupName"),
                "ip": ap.get("ip"),
                "mac": ap.get("apMac"),
                "serial": ap.get("serial"),
                "status": ap.get("configurationStatus"),
                "current_clients": ap.get("numClients"),
                "address": ap.get("location")}
                )
        return aps_list_dic
    # ---------- Cambia configuración de un AP dada una MAC ----------
    def change_config_1ap(self, ap_mac: str, config: Dict):

        endpoint = f"{self.base_url}/aps/{ap_mac}"
        response = self.session.patch(endpoint, json=config, verify=False)
        response.raise_for_status()
        print(f"Configuración del AP {ap_mac} actualizada correctamente.")
    
    def config_aps(self, ap_list: List[Dict]):
        """
        Configura los APs en la lista proporcionada.
        """
        for ap in ap_list:
            mac = ap.get("mac")
            config = {
                "name": ap.get("name"),
                "description": ap.get("description"),
                "location": ap.get("address")
            }
            self.change_config_1ap(mac, config)
            sleep(0.5)  # Espera 0.5 segundos entre configuraciones para evitar sobrecarga
        self.session.close()


    def close(self):
        """
        Cierra la sesión y elimina el token de autenticación.
        """
        self.session.close()
        self.token = None
# ------------------ Ejecución directa ------------------ #


def main():
    
    controller_ip = " "  # IP del SmartZone
    username = "  "  # Usuario por defecto
    password = " "  # Contraseña por defecto
    # domain_id = "7eee9134-2ba8-4441-80ea-13b47611261c"  # ID del dominio por defecto
    api = SmartZoneAPI(controller_ip, username, password)
    mac = " "
    config = {
        "name": " ",
        "description": " ",
        "location": " "
    }

    api.change_config_1ap(mac, config)

    """
    dic_domain = api.get_domains()

    pprint(dic_domain) 
    
    if dic_domain == [] :
        domain_id = '0'
    else:
        domain_id = input("Digite ID de Dominio: ")
    
    raw_aps = api.query_aps_by_domain(domain_id)

    print("\nConsultando APs…")
    print(f"Total de APs encontrados: {len(raw_aps)}\n")
    pprint(raw_aps)

   """
    


if __name__ == "__main__":
    main()


